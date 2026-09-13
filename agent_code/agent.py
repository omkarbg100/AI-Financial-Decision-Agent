from langgraph.graph import StateGraph, END
from state import GraphState
from nodes import gather_context_node, process_unstructured_node, simulation_node, generate_explanation_node

def build_financial_agent(data_loader):
    # Initialize StateGraph with our state schema
    workflow = StateGraph(GraphState)

    # Wrap nodes to pass data_loader where needed
    def gather_wrapper(state):
        return gather_context_node(state, data_loader)
        
    def unstructured_wrapper(state):
        return process_unstructured_node(state, data_loader)
        
    def simulation_wrapper(state):
        return simulation_node(state, data_loader)

    # Add nodes to graph
    workflow.add_node("gather_context", gather_wrapper)
    workflow.add_node("process_unstructured", unstructured_wrapper)
    workflow.add_node("simulate", simulation_wrapper)
    workflow.add_node("explain", generate_explanation_node)

    # Add edges
    workflow.set_entry_point("gather_context")
    workflow.add_edge("gather_context", "process_unstructured")
    workflow.add_edge("process_unstructured", "simulate")
    workflow.add_edge("simulate", "explain")
    workflow.add_edge("explain", END)

    # Compile the graph
    agent = workflow.compile()
    
    return agent
