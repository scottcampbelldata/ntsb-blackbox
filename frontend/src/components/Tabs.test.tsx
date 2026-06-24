import { describe, it, expect } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { Tabs } from "./Tabs";

const tabs = [
  { id: "sql", label: "SQL", content: <p>the sql</p> },
  { id: "table", label: "Table", content: <p>the table</p> }
];

describe("Tabs", () => {
  it("shows the first tab by default and switches on click", () => {
    const { getByRole, getByText, queryByText } = render(<Tabs tabs={tabs} />);
    expect(getByText("the sql")).toBeInTheDocument();
    expect(queryByText("the table")).toBeNull();
    fireEvent.click(getByRole("tab", { name: "Table" }));
    expect(getByText("the table")).toBeInTheDocument();
    expect(queryByText("the sql")).toBeNull();
  });

  it("renders nothing when there are no tabs", () => {
    const { container } = render(<Tabs tabs={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
