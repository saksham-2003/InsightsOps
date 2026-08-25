import { Search } from "lucide-react";

function Topbar({ title, subtitle, setActivePage }) {
  return (
    <header className="topbar">
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <button
          className="ask-ai-button"
          onClick={() => {
              console.log("ASK AI BUTTON CLICKED");
              console.log("setActivePage:", setActivePage);
              setActivePage("ai-analyst");
          }}
      >
          <Search size={17} />
          Ask InsightsOps AI
      </button>
    </header>
  );
}

export default Topbar;