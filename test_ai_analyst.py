"""
End-to-End Integration Test Suite for InsightsOps AI Analyst.

This script verifies the complete production AI Analyst pipeline from natural language
query input through metadata loading, entity extraction, conversation memory management,
AI planning, dynamic tool routing, and analytics execution.
"""

import time
import traceback
import sys
import pandas as pd
from typing import Dict, Any, List

# Import actual production modules and workflows
from src.agents.agent_workflow import run_insightsops_agent
from src.agents.state import ConversationMemoryManager
from src.agents.metadata_loader import MetadataLoader
from src.agents.entity_extractor import EntityExtractor
from src.agents.planner import create_ai_plan
from src.agents.router import route_query


def load_test_dataframe() -> pd.DataFrame:
    """
    Loads or generates a mock/sample cleaned DataFrame representing 
    enterprise business data for testing if no dataset file is directly present.
    """
    try:
        # Attempt to load using standard project cleaning pipelines if available, 
        # otherwise create a robust sample DataFrame conforming to expected schema.
        from src.data_cleaner import clean_data
        # Try loading a typical sample file path or create synthetic test frame
        df = pd.read_csv("sample_data.csv")
        return clean_data(df)
    except Exception:
        # Fallback to rich mock dataset covering all required dimensions and categories
        data = {
            "Order_Date": pd.date_range(start="2023-01-01", periods=100, freq="D"),
            "Region": ["East", "West", "North", "South", "Central"] * 20,
            "Country": ["United States"] * 100,
            "State": ["California", "New York", "Texas", "Washington", "Florida"] * 20,
            "City": ["Los Angeles", "New York City", "Houston", "Seattle", "Miami"] * 20,
            "Category": ["Electronics", "Furniture", "Office Supplies", "Technology", "Apparel"] * 20,
            "Sub_Category": ["Phones", "Chairs", "Paper", "Laptops", "Shirts"] * 20,
            "Product_Name": ["MacBook Air", "Office Chair", "Printer Paper", "Dell XPS", "T-Shirt"] * 20,
            "Customer_Name": ["Acme Corp", "Beta LLC", "Gamma Inc", "Delta Co", "Omega Ltd"] * 20,
            "Order_ID": [f"ORD-{i:04d}" for i in range(100)],
            "Quantity": [1, 2, 5, 3, 4] * 20,
            "Unit_Price": [1200.0, 150.0, 20.0, 950.0, 25.0] * 20,
            "Revenue": [1200.0, 300.0, 100.0, 2850.0, 100.0] * 20,
            "Profit": [300.0, 50.0, 10.0, 700.0, 20.0] * 20,
            "Customer_ID": [f"CUST-{i%10:03d}" for i in range(100)]
        }
        df = pd.DataFrame(data)
        df["Order_Date"] = pd.to_datetime(df["Order_Date"])
        # Shift the entire dataset by 3 years
        df["Order_Date"] = df["Order_Date"] + pd.DateOffset(years=3)
        print(df["Order_Date"].min())
        print(df["Order_Date"].max())
        return df


def get_test_queries() -> List[str]:
    """
    Returns a comprehensive list of around 30 realistic business queries 
    spanning KPIs, Regions, Categories, Time, Products, Forecasts, Anomalies, and Complex logic.
    """
    return [
        # General KPI
        "Show business summary",
        "Give me overall KPIs",
        "Show revenue and profit",
        
        # Region
        "Show sales in West region",
        "Analyze South region",
        "Compare East and West",
        
        # Category
        "Analyze Electronics",
        "Show Furniture performance",
        "Which category performs best",
        
        # Time
        "Show revenue in 2024",
        "Show March 2023 performance",
        "Show last year's revenue",
        
        # Combined
        "Show Electronics revenue in West region during 2024",
        "Show Furniture sales in East in March",
        "Analyze Technology category in North",
        
        # Products
        "Top products",
        "Best selling Electronics products",
        "Highest revenue products",
        
        # Forecast
        "Forecast revenue",
        "Forecast Electronics revenue",
        "Predict next month's revenue",
        
        # Anomaly
        "Show anomalies",
        "Show critical anomalies",
        "Analyze suspicious transactions",
        
        # Complex
        "Compare Electronics and Furniture",
        "Find the weakest region",
        "Which region has highest profit",
        "Show category contribution in West",
        "Show orders in Q1",
        "Analyze average profit by category"
    ]


def run_integration_tests() -> None:
    """
    Executes end-to-end integration tests across all sample queries using 
    the production InsightsOps agent workflow, capturing metrics and handling errors gracefully.
    """
    print("Initializing InsightsOps Test Suite...")
    df = load_test_dataframe()
    
    # Initialize shared components for standalone verification steps matching workflow
    metadata_loader = MetadataLoader(df)
    business_metadata = metadata_loader.load()
    extractor = EntityExtractor(business_metadata)
    memory_manager = ConversationMemoryManager(session_id="test-session-integration")

    queries = get_test_queries()
    total_queries = len(queries)
    passed_count = 0
    failed_count = 0
    total_execution_time = 0.0

    print(f"Loaded {len(df)} records. Starting execution of {total_queries} test queries...\n")

    for idx, query in enumerate(queries, start=1):
        print("=" * 60)
        print(f"Query {idx}/{total_queries}")
        print("=" * 60)
        print(query)
        print("-" * 60)

        start_time = time.perf_counter()
        
        try:
            # 1. Extract entities directly to inspect in test logs
            extracted = extractor.extract(query)
            entities_dict = vars(extracted) if extracted else {}

            # 2. Run through the full production agent workflow
            result = run_insightsops_agent(query, df, memory_manager=memory_manager)

            elapsed_time = time.perf_counter() - start_time
            total_execution_time += elapsed_time

            if not result.get("success", False):
                raise RuntimeError(f"Workflow reported failure: {result.get('errors', 'Unknown error')}")

            plan = result.get("plan", {})
            execution = result.get("execution", {})
            exec_meta = execution.get("metadata", {})
            
            selected_tools = plan.get("selected_tools", [])
            tool_exec_plan = plan.get("tool_execution_plan", [])
            
            # Extract arguments used from execution metadata or tool execution plan
            tool_args_used = exec_meta.get("tool_arguments_used", {})
            if not tool_args_used and tool_exec_plan:
                for entry in tool_exec_plan:
                    if isinstance(entry, dict):
                        tool_args_used[entry.get("tool")] = entry.get("arguments", {})

            print("Entities")
            print("-" * 60)
            print(entities_dict)
            
            print("\nPlanner Output")
            print("-" * 60)
            print(plan)
            
            print("\nSelected Tool")
            print("-" * 60)
            print(selected_tools)
            
            print("\nTool Arguments")
            print("-" * 60)
            print(tool_args_used)
            
            print("\nResponse")
            print("-" * 60)
            # Print executive summary or truncated final response safely
            final_resp = result.get("final_response", {})
            print(final_resp if final_resp else result.get("context", "No response context"))
            
            print("\nExecution Time")
            print("-" * 60)
            print(f"{elapsed_time:.2f} sec\n")

            passed_count += 1

        except Exception as e:
            elapsed_time = time.perf_counter() - start_time
            total_execution_time += elapsed_time
            failed_count += 1

            print("\nERROR")
            print("-" * 60)
            print(f"Failed to execute query: {query}")
            traceback.print_exc()
            print(f"\nExecution Time: {elapsed_time:.2f} sec\n")

    # Final Summary Calculation
    success_rate = (passed_count / total_queries) * 100 if total_queries > 0 else 0.0
    avg_execution_time = (total_execution_time / total_queries) if total_queries > 0 else 0.0

    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total Queries        : {total_queries}")
    print(f"Passed               : {passed_count}")
    print(f"Failed               : {failed_count}")
    print(f"Success Rate         : {success_rate:.2f}%")
    print(f"Average Execution Time: {avg_execution_time:.2f} sec")
    print("=" * 60)


if __name__ == "__main__":
    run_integration_tests()