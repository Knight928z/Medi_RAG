from agents.memory import MemoryAgent
from agents.parser import ParserAgent
from agents.planner import PlannerAgent
from agents.reasoning import ReasoningAgent
from agents.retriever import RetrieverAgent
from agents.validator import ValidatorAgent


def build_nodes():
    return {
        "planner": PlannerAgent(),
        "parser": ParserAgent(),
        "retriever": RetrieverAgent(),
        "reasoning": ReasoningAgent(),
        "validator": ValidatorAgent(),
        "memory": MemoryAgent(),
    }
