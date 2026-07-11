import { Search } from "lucide-react";

function Topbar({ title, subtitle }) {
  return (
    <header className="topbar">
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <button className="ask-ai-button">
        <Search size={17} />
        Ask InsightsOps AI
      </button>
    </header>
  );
}

export default Topbar;