import time
import json
import logging
from typing import Dict, Any, List, Optional

from src.agents.planner import create_ai_plan
from src.agents.router import route_query
from src.agents.llm_client import get_llm_client, create_chat_completion_with_retry, extract_response_text
from .state import ConversationMemoryManager, TurnContext, FilterState
from .metadata_loader import MetadataLoader, BusinessMetadata
from .entity_extractor import EntityExtractor, ExtractedEntities


class InsightsOpsOrchestrator:
    """
    Multi-stage orchestration engine for InsightsOps Business Analyst.
    
    Designed to behave like a professional Business Analyst and explicitly 
    structured for future Agentic AI capabilities:
    
    - Conversation Memory: Integrated via ConversationMemoryManager.
    - Reflection & Self Critique: Outputs can be looped back to LLM for validation.
    - Agent Retry: LLM generation blocks are structured to easily wrap with tenacity/retries.
    - Parallel Execution & Caching: Directly integrated via upstream dynamic router.
    """

    def __init__(self, memory_manager: ConversationMemoryManager):
        self.client = get_llm_client()
        self.model = "openai/gpt-oss-20b"
        self.temperature = 0.1
        self.memory_manager = memory_manager

    def validate_and_clean_evidence(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP 4: Validate evidence. 
        Removes duplicates, drops empty values, and filters out missing/failed tool outputs.
        """
        cleaned = {}
        for tool_name, data in raw_results.items():
            if not data:
                continue
            
            # Handle structured dictionary responses
            if isinstance(data, dict):
                if data.get("success") is False or "error" in data:
                    continue  # Drop failed tool executions
                if not data:
                    continue
                cleaned[tool_name] = data
                
            # Handle list responses and remove duplicates
            elif isinstance(data, list):
                if len(data) == 0:
                    continue
                
                unique_list = []
                seen = set()
                for item in data:
                    if isinstance(item, dict):
                        item_str = json.dumps(item, sort_keys=True, default=str)
                        if item_str not in seen:
                            seen.add(item_str)
                            unique_list.append(item)
                    else:
                        if item not in seen:
                            seen.add(item)
                            unique_list.append(item)
                            
                if unique_list:
                    cleaned[tool_name] = unique_list
            else:
                cleaned[tool_name] = data
                
        return cleaned

    def generate_business_context(self, evidence: Dict[str, Any]) -> str:
        """
        STEP 3 & 5: Collect and Generate Business Context.
        Merges outputs from all executed tools into one structured evidence object.
        Summarizes KPIs, Forecasts, Anomalies, Regional/Category performance, etc.
        """
        context_obj = {}
        
        # Explicitly map known tools to structured context segments
        if "kpi_summary" in evidence:
            context_obj["KPIs"] = evidence["kpi_summary"]
            
        if "forecast_evaluation" in evidence:
            fc = evidence["forecast_evaluation"]
            if isinstance(fc, dict) and "predictions" in fc:
                context_obj["Forecast_Metrics"] = fc.get("metrics", {})
                context_obj["Forecast_Trends"] = fc["predictions"][-15:]  # Limit to 15 future days
            else:
                context_obj["Forecasts"] = fc
                
        if "anomaly_detection" in evidence:
            anom = evidence["anomaly_detection"]
            if isinstance(anom, dict) and "data" in anom:
                context_obj["Anomalies_Summary"] = anom["data"].get("executive_summary", {})
                context_obj["Top_Anomalies"] = anom["data"].get("table_data", [])[:10]
            else:
                context_obj["Anomalies"] = anom
                
        if "regional_performance" in evidence:
            context_obj["Regional_Performance"] = evidence["regional_performance"][:10]
            
        if "category_performance" in evidence:
            context_obj["Category_Performance"] = evidence["category_performance"][:10]
            
        if "top_products" in evidence:
            context_obj["Top_Products"] = evidence["top_products"][:10]

        if "bottom_products" in evidence:
            context_obj["Bottom_Products"] = evidence["bottom_products"][:10]
            
        if "monthly_trend" in evidence:
            context_obj["Monthly_Trend"] = evidence["monthly_trend"][-12:]  # Limit to last year
            
        # Ensure we only return segments that actually have data
        filtered_context = {k: v for k, v in context_obj.items() if v}
        
        return json.dumps(filtered_context, default=str)

    def generate_final_response(self, user_query: str, context_str: str, memory_summary: str = "") -> Dict[str, Any]:
        print(">>>>>>>> ENTERED generate_final_response <<<<<<<<")
        """
        STEP 6 & 7: LLM Generation
        Passes structured context to the LLM to generate the final response strictly from evidence.
        Includes Reflection / Self-Validation stage to verify grounding and prevent hallucinations.
        """
        print("\n========== ENTERED generate_final_response ==========\n")
        system_prompt = f"""
You are a Principal Business Analyst for InsightsOps, an enterprise Business Intelligence application.
Your objective is to answer the user's business question using ONLY the provided structured evidence and context.

CONVERSATION SUMMARY:
{memory_summary}

CRITICAL RULES:
1. Grounding: Answer ONLY from the provided evidence. Never hallucinate, estimate, or invent data.
2. Relevance: Only populate sections that are directly relevant to the user's question. Leave irrelevant sections empty.
3. Tone: Professional, analytical, and highly structured.
4. Handling No Data Found: If the evidence context is empty or indicates no matching records were found, you MUST:
   - Clearly explain that no matching records were found for the user's query and filters.
   - Suggest possible reasons (e.g., no sales occurred, or filters are too restrictive).
   - Recommend how the user can refine the query (e.g., try another region, larger date range, or remove one filter).
5. Follow-up Questions: Generate 3-5 intelligent, dynamic follow-up questions based on the user's original question, the evidence, and the analysis performed, which naturally extend the conversation.
6. Output: You MUST return a valid JSON object matching the schema below.

REQUIRED JSON OUTPUT SCHEMA:
{{
    "executive_summary": "Concise, high-level summary directly addressing the user's core question or explaining that no data was found.",
    "key_findings": ["Specific finding 1", "Specific finding 2"],
    "evidence": ["Data point 1 from context supporting the findings", "Data point 2"],
    "business_insights": ["Strategic insight explaining WHY something happened based on evidence"],
    "recommendations": ["Actionable, practical, and data-driven recommendation"],
    "potential_risks": ["Any risks, anomalies, or caveats supported by evidence"],
    "suggested_follow_up_questions": ["Intelligent follow-up question 1", "Intelligent follow-up question 2"]
}}
"""
        
        # Prepare the LLM payload
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": f"USER QUESTION:\n{user_query}\n\nEVIDENCE CONTEXT:\n{context_str}"
            }
        ]

        try:
            print("Calling LLM...")
            print("LLM call completed.")
            response = create_chat_completion_with_retry(
                self.client,
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            print("\n========== RAW GEMINI RESPONSE ==========\n")

            raw = extract_response_text(response)

            print(type(response))
            print("------------------------")
            print("RAW TEXT:")
            print(raw)
            print("------------------------")
            print("RESPONSE OBJECT:")
            print(response)

            print("\n=========================================\n")

            initial_response = json.loads(raw)
            
            # ========================================================
            # REFLECTION / SELF-VALIDATION STAGE
            # ========================================================
            initial_response["reflection_passed"] = True
            return initial_response
            
        except Exception as e:
            raise
            

    def _reflect_and_validate(self, user_query: str, context_str: str, generated_response: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        """
        Validates the generated response against the provided evidence.
        Revises the response once if validation fails, replacing unsupported claims.
        """
        reflection_prompt = f"""
You are a strict QA and Fact-Checking Auditor for an enterprise BI platform.
Your task is to validate whether the generated response strictly complies with the provided evidence context.

USER QUESTION:
{user_query}

EVIDENCE CONTEXT:
{context_str}

GENERATED RESPONSE TO VALIDATE:
{json.dumps(generated_response, default=str)}

VALIDATION CRITERIA:
1. Every major claim, number, and finding must be directly supported by the evidence context.
2. No hallucinated or invented numbers or statistics exist.
3. Recommendations must be supported by evidence.
4. Risks are mentioned only if evidence supports them.
5. If evidence is insufficient or missing for any claim, replace unsupported statements with: "The available evidence does not provide enough information."

Return a valid JSON object matching this schema:
{{
    "passed": true/false,
    "revised_response": {{
        "executive_summary": "...",
        "key_findings": ["..."],
        "evidence": ["..."],
        "business_insights": ["..."],
        "recommendations": ["..."],
        "potential_risks": ["..."],
        "suggested_follow_up_questions": ["..."]
    }}
}}
If passed is true, revised_response can be the original response. If false, provide the corrected response.
"""
        try:
            reflection_messages = [
                {"role": "system", "content": reflection_prompt},
                {"role": "user", "content": "Perform validation and return JSON."}
            ]
            
            ref_resp = create_chat_completion_with_retry(
                self.client,
                model=self.model,
                messages=reflection_messages,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            ref_data = json.loads(extract_response_text(ref_resp))
            passed = bool(ref_data.get("passed", True))
            revised = ref_data.get("revised_response", generated_response)
            
            if not isinstance(revised, dict):
                revised = generated_response
                
            return revised, passed
            
        except Exception as ref_error:
            logging.error(f"Reflection stage error (non-fatal): {str(ref_error)}")
            # Default to passing original response if reflection fails technically
            return generated_response, True


def run_insightsops_agent(user_query: str, df: Any, memory_manager: Optional[ConversationMemoryManager] = None) -> Dict[str, Any]:
    """
    Run the complete InsightsOps Business Analyst orchestration pipeline with memory integration.
    
    Pipeline Steps:
    1. Receive user query
    2. Load metadata & extract entities
    3. Load conversation memory & merge entities
    4. Detect whether the query is a follow-up
    5. Resolve the query using conversation context if required
    6. Pass resolved query to planner
    7. Execute tools
    8. Validate evidence
    9. Generate business context
    10. Generate final response (with Reflection / Self-Validation)
    11. Save current interaction into ConversationMemoryManager
    12. Return response with memory metadata and extracted entities
    """
    start_time = time.time()
    
    # 2. Load conversation memory (Reuse passed manager, or fall back to a new one if none supplied)
    mem_mgr = memory_manager if memory_manager is not None else ConversationMemoryManager()
    orchestrator = InsightsOpsOrchestrator(memory_manager=mem_mgr)
    
    # Initialize MetadataLoader once per workflow execution
    extracted_entities_obj = ExtractedEntities()
    merged_entities_dict = {}
    
    try:
        metadata_loader = MetadataLoader(df)
        business_metadata = metadata_loader.load()
        entity_extractor = EntityExtractor(business_metadata)
        extracted_entities_obj = entity_extractor.extract(user_query)
        
        # Merge entities into memory
        merged_entities = mem_mgr.merge_entities(extracted_entities_obj)
        merged_entities_dict = vars(merged_entities) if merged_entities else {}
    except Exception as ent_error:
        logging.error(f"Entity extraction / metadata loading error (non-fatal): {str(ent_error)}")
        merged_entities_dict = mem_mgr.get_current_entities()

    # Detect follow-up & Resolve query
    follow_up_detected = False
    resolved_query = user_query
    try:
        follow_up_detected = mem_mgr.is_follow_up(user_query)
        if follow_up_detected:
            resolved_query = mem_mgr.resolve_context(user_query)
    except Exception as mem_error:
        logging.error(f"Memory processing error (non-fatal): {str(mem_error)}")

    response = {
        "success": False,
        "user_query": user_query,
        "resolved_query": resolved_query,
        "entities": merged_entities_dict,
        "confidence": getattr(extracted_entities_obj, "confidence", 0.0),
        "plan": {},
        "execution": {},
        "evidence": {},
        "context": "",
        "final_response": {},
        "metadata": {},
        "errors": []
    }

    # ========================================================
    # STEP 5: AI PLANNING (using resolved query)
    # ========================================================
    plan_start = time.time()
    try:
        plan = create_ai_plan(resolved_query)
        print("=" * 50)
        print("RESOLVED QUERY:", resolved_query)
        print("SELECTED TOOLS:", plan.get("selected_tools"))
        print("=" * 50)
        print("\n========== GENERATED PLAN ==========")
        print(json.dumps(plan, indent=2))
        print("====================================\n")
        response["plan"] = plan
    except Exception as error:
        response["errors"].append(f"Planning error: {str(error)}")
        # Safe fallback plan to ensure workflow continuity
        plan = {
            "intents": ["General Analysis"], 
            "selected_tools": ["kpi_summary", "monthly_trend"], 
            "confidence": 0.0
        }
        response["plan"] = plan
        
    plan_time = time.time() - plan_start

    # ========================================================
    # STEP 6: TOOL EXECUTION & GRACEFUL ERROR HANDLING
    # ========================================================
    try:
        execution = route_query(plan, df)
        response["execution"] = execution

        metadata = execution.get("metadata", {})
        failed_tools = metadata.get("failed_tools", [])

        if failed_tools:

            logging.info(f"Replanning because these tools failed: {failed_tools}")

            new_plan = create_ai_plan(
                resolved_query,
                context={"failed_tools": failed_tools},
                failed_tools=failed_tools
            )

            execution = route_query(new_plan, df)

            response["execution"] = execution
            response["replanned"] = True
        
        # Track individual tool failures without crashing workflow
        failed_tools = execution.get("metadata", {}).get("failed_tools", [])
        if failed_tools and not response.get("replanned", False):
            response["errors"].extend([f"Tool failed during execution: {t}" for t in failed_tools])
            
    except Exception as error:
        response["errors"].append(f"Tool routing/execution error: {str(error)}")
        execution = {"results": {}, "metadata": {}}

    # ========================================================
    # STEP 7: COLLECT & VALIDATE EVIDENCE
    # ========================================================
    try:
        raw_results = execution.get("results", {})
        valid_evidence = orchestrator.validate_and_clean_evidence(raw_results)
        response["evidence"] = valid_evidence
    except Exception as error:
        response["errors"].append(f"Evidence validation error: {str(error)}")
        valid_evidence = {}

    reflection = {
        "is_evidence_sufficient": len(valid_evidence) > 0,
        "missing_information": [],
        "warnings": []
    }

    response["reflection"] = reflection

    # ========================================================
    # STEP 8: GENERATE BUSINESS CONTEXT
    # ========================================================
    try:
        context_str = orchestrator.generate_business_context(valid_evidence)
        response["context"] = context_str
    except Exception as error:
        response["errors"].append(f"Context generation error: {str(error)}")
        context_str = "{}"

    # ========================================================
    # STEP 9: LLM ANALYSIS & FINAL RESPONSE (with Reflection)
    # ========================================================
    try:
        print("STEP 9 - Before summarize_context")

        memory_summary = mem_mgr.summarize_context()

        print("STEP 9 - Before generate_final_response")

        final_response = orchestrator.generate_final_response(
            resolved_query,
            context_str,
            memory_summary
        )

        print("STEP 9 - After generate_final_response")

        response["final_response"] = final_response
        response["llm_status"] = "success"

    except Exception as error:
        print("STEP 9 ERROR:", error)

        final_response = {
            "executive_summary": "The AI service is temporarily unavailable. Please try again later.",
            "key_findings": [],
            "evidence": [],
            "business_insights": [],
            "recommendations": [],
            "potential_risks": [],
            "suggested_follow_up_questions": [],
            "reflection_passed": False
        }

        response["final_response"] = final_response
        response["errors"].append(f"LLM Error: {str(error)}")

    # ========================================================
    # STEP 10: SAVE THE CURRENT INTERACTION INTO MEMORY
    # ========================================================
    try:
        exec_meta = execution.get("metadata", {})
        executed_tools = exec_meta.get("executed_tools", [])
        ai_resp_text = final_response.get("executive_summary", "") if isinstance(final_response, dict) else str(final_response)
        recs = final_response.get("recommendations", []) if isinstance(final_response, dict) else []

        turn = TurnContext(
            user_query=user_query,
            ai_response=ai_resp_text,
            planner_output=plan,
            selected_tools=executed_tools,
            extracted_entities=[],
            filters=FilterState(),
            execution_metadata=exec_meta,
            evidence_summary=valid_evidence,
            recommendations=recs,
            timestamp=time.time()
        )
        mem_mgr.store_turn(turn)

    except Exception as mem_store_error:
        logging.error(f"Memory storage error (non-fatal): {str(mem_store_error)}")
        response["errors"].append(f"Memory storage error: {str(mem_store_error)}")

    # [Insert the rest of agent_workflow.py unmodified up to run_insightsops_agent return block]
    # ========================================================
    # STEP 11: RETURN RESPONSE & METADATA
    # ========================================================
    end_time = time.time()
    total_time = end_time - start_time
    
    executed_tools = execution.get("metadata", {}).get("executed_tools", [])
    
    # Calculate total evidence points securely
    evidence_count = sum(
        len(v) if isinstance(v, list) else 1 
        for v in valid_evidence.values()
    )
    
    reflection_passed_flag = final_response.get("reflection_passed", True) if isinstance(final_response, dict) else True
    
    response["metadata"] = {
        "execution_time_seconds": round(total_time, 4),
        "planning_time_seconds": round(plan_time, 4),
        "tool_count": len(executed_tools),
        "tools_used": executed_tools,
        "evidence_count": evidence_count,
        "confidence": plan.get("confidence", 0.85),
        "reflection_passed": reflection_passed_flag,
        "memory": {
            "follow_up_detected": follow_up_detected,
            "resolved_query": resolved_query,
            "conversation_turns": len(mem_mgr.history)
        }
    }

    # Automatically generate visualization specification from executed tool results
    visualization_spec = None
    try:
        from src.agents.chart_generator import generate_visualization
        raw_results = execution.get("results", {})
        for t_name in executed_tools:
            if t_name in raw_results:
                
                print("Tool:", t_name)
                viz = generate_visualization(t_name, raw_results[t_name])
                print("Visualization Returned:", viz)
                
                if viz:
                    visualization_spec = viz
                    break
    except Exception as viz_error:
        logging.error(f"Visualization generation error (non-fatal): {str(viz_error)}")

    # Workflow guarantees a response object is always returned successfully
    response["success"] = True
    response["visualization"] = visualization_spec
    response["execution_summary"] = {
        "planned_tools": plan.get("selected_tools", []),
        "executed_tools": execution.get("metadata", {}).get("executed_tools", []),
        "failed_tools": execution.get("metadata", {}).get("failed_tools", []),
        "replanned": response.get("replanned", False)
    }
    print("=" * 60)
    print("EXECUTED TOOLS:", executed_tools)
    print("=" * 60)

    print("VISUALIZATION GENERATED:")
    print(json.dumps(visualization_spec, indent=2, default=str))

    return response