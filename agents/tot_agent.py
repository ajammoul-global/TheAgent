"""
Tree of Thoughts (ToT) Agent Implementation
Explores multiple reasoning paths and selects the best solution
"""
from typing import List, Dict, Any, Optional, Tuple
from models.base import BaseModel
from infra.tool_registry import ToolRegistry
from infra.logging import logger
import json


class TreeNode:
    """Represents a node in the reasoning tree"""
    
    def __init__(self, content: str, depth: int = 0, parent: Optional['TreeNode'] = None):
        self.content = content
        self.depth = depth
        self.parent = parent
        self.children: List['TreeNode'] = []
        self.score: Optional[float] = None
        self.evaluation: Optional[str] = None
    
    def add_child(self, child: 'TreeNode'):
        """Add child node"""
        self.children.append(child)
        child.parent = self
    
    def get_path(self) -> List[str]:
        """Get full path from root to this node"""
        path = []
        node = self
        while node:
            path.append(node.content)
            node = node.parent
        return list(reversed(path))
    
    def __repr__(self):
        return f"TreeNode(depth={self.depth}, score={self.score}, content={self.content[:50]}...)"


class TreeOfThoughtsAgent:
    """
    Tree of Thoughts agent that:
    1. Generates multiple reasoning paths
    2. Evaluates each path
    3. Selects and refines best path
    4. Executes optimal solution
    
    Best for: Complex decisions, planning, problem-solving
    """
    
    def __init__(
        self, 
        model: BaseModel, 
        registry: ToolRegistry,
        num_branches: int = 3,
        max_depth: int = 2,
        evaluation_criteria: Optional[List[str]] = None
    ):
        """
        Initialize ToT agent
        
        Args:
            model: Language model for reasoning
            registry: Tool registry for actions
            num_branches: Number of paths to explore at each level
            max_depth: How deep to build the tree
            evaluation_criteria: Custom criteria for evaluating paths
        """
        self.model = model
        self.registry = registry
        self.num_branches = num_branches
        self.max_depth = max_depth
        self.evaluation_criteria = evaluation_criteria or [
            "Feasibility",
            "Effectiveness", 
            "Efficiency",
            "Risk"
        ]
        logger.info(
            f"ToT agent initialized: {num_branches} branches, "
            f"{max_depth} depth, {len(registry)} tools"
        )
    
    def run(self, query: str) -> str:
        """
        Execute Tree of Thoughts reasoning
        
        Args:
            query: User's question or problem
            
        Returns:
            Final answer based on best path
        """
        logger.info(f"ToT agent starting: {query}")
        
        # Phase 1: Build reasoning tree
        root = TreeNode(content=f"Query: {query}", depth=0)
        self._build_tree(root, query)
        
        # Phase 2: Evaluate all paths
        leaf_nodes = self._get_leaf_nodes(root)
        evaluated_paths = self._evaluate_paths(leaf_nodes, query)
        
        # Phase 3: Select best path
        best_path = self._select_best_path(evaluated_paths)
        
        # Phase 4: Execute actions if needed
        observation = self._execute_if_needed(best_path, query)
        
        # Phase 5: Generate final answer
        answer = self._final_answer(query, best_path, observation)
        
        return answer
    
    def _build_tree(self, node: TreeNode, query: str):
        """
        Recursively build reasoning tree
        
        Args:
            node: Current node
            query: Original query
        """
        if node.depth >= self.max_depth:
            return
        
        logger.info(f"Building tree at depth {node.depth + 1}...")
        
        # Generate branches
        branches = self._generate_branches(node, query)
        
        for i, branch_content in enumerate(branches, 1):
            child = TreeNode(
                content=branch_content,
                depth=node.depth + 1,
                parent=node
            )
            node.add_child(child)
            logger.info(f"  Branch {i}: {branch_content[:80]}...")
            
            # Recursively build deeper
            self._build_tree(child, query)
    
    def _generate_branches(self, node: TreeNode, query: str) -> List[str]:
        """
        Generate multiple reasoning branches
        
        Args:
            node: Current node
            query: Original query
            
        Returns:
            List of branch contents
        """
        # Build context from path
        path = node.get_path()
        context = "\n".join([f"Step {i+1}: {p}" for i, p in enumerate(path)])
        
        prompt = f"""Original question: {query}

Current reasoning path:
{context}

Generate {self.num_branches} DIFFERENT possible next steps or approaches.
Each should be a distinct way to proceed.

For depth {node.depth + 1}, consider:
- Different strategies
- Alternative perspectives  
- Various solutions

Respond with ONLY a JSON array of {self.num_branches} distinct options:
["option 1", "option 2", "option 3"]

JSON:"""
        
        response = self.model.generate(prompt, max_tokens=300, temperature=0.8)
        
        try:
            # Parse JSON array
            response = response.strip()
            if "```" in response:
                parts = response.split("```")
                for part in parts:
                    if "[" in part:
                        response = part.replace("json", "").strip()
                        break
            
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end > start:
                branches = json.loads(response[start:end])
                
                # Ensure we have the right number
                if len(branches) < self.num_branches:
                    logger.warning(f"Got {len(branches)} branches, expected {self.num_branches}")
                
                return branches[:self.num_branches]
                
        except Exception as e:
            logger.error(f"Failed to parse branches: {e}")
        
        # Fallback: generate generic branches
        return [f"Approach {i+1} for the problem" for i in range(self.num_branches)]
    
    def _get_leaf_nodes(self, root: TreeNode) -> List[TreeNode]:
        """Get all leaf nodes (end of paths)"""
        leaves = []
        
        def traverse(node):
            if not node.children:
                leaves.append(node)
            else:
                for child in node.children:
                    traverse(child)
        
        traverse(root)
        logger.info(f"Found {len(leaves)} complete paths to evaluate")
        return leaves
    
    def _evaluate_paths(self, leaf_nodes: List[TreeNode], query: str) -> List[Dict]:
        """
        Evaluate each complete path
        
        Returns:
            List of dicts with path, score, and evaluation
        """
        logger.info(f"Evaluating {len(leaf_nodes)} paths...")
        evaluated = []
        
        for i, leaf in enumerate(leaf_nodes, 1):
            path = leaf.get_path()
            path_str = "\n".join([f"Step {j+1}: {p}" for j, p in enumerate(path)])
            
            # Get evaluation
            score, evaluation = self._evaluate_single_path(path_str, query)
            
            evaluated.append({
                'path': path,
                'path_str': path_str,
                'score': score,
                'evaluation': evaluation,
                'node': leaf
            })
            
            logger.info(f"  Path {i}: Score {score}/10")
            logger.info(f"          {evaluation[:100]}...")
        
        # Sort by score
        evaluated.sort(key=lambda x: x['score'], reverse=True)
        return evaluated
    
    def _evaluate_single_path(self, path_str: str, query: str) -> Tuple[float, str]:
        """
        Evaluate a single path
        
        Returns:
            (score, evaluation_text)
        """
        criteria_str = ", ".join(self.evaluation_criteria)
        
        prompt = f"""Original question: {query}

Reasoning path to evaluate:
{path_str}

Evaluate this path based on: {criteria_str}

Respond with ONLY valid JSON:
{{
    "score": 7.5,
    "evaluation": "This path is good because... However...",
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1"]
}}

Score should be 0-10 (10 is best).

JSON:"""
        
        response = self.model.generate(prompt, max_tokens=300, temperature=0.3)
        
        try:
            # Parse JSON
            response = response.strip()
            if "```" in response:
                parts = response.split("```")
                for part in parts:
                    if "{" in part:
                        response = part.replace("json", "").strip()
                        break
            
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                eval_data = json.loads(response[start:end])
                return eval_data.get('score', 5.0), eval_data.get('evaluation', 'No evaluation')
                
        except Exception as e:
            logger.warning(f"Failed to parse evaluation: {e}")
        
        return 5.0, "Could not evaluate path"
    
    def _select_best_path(self, evaluated_paths: List[Dict]) -> Dict:
        """Select the highest-scoring path"""
        best = evaluated_paths[0]
        logger.info(f"✓ Selected best path with score: {best['score']}/10")
        logger.info(f"  Evaluation: {best['evaluation'][:150]}...")
        return best
    
    def _execute_if_needed(self, best_path: Dict, query: str) -> Optional[str]:
        """
        Determine if tools are needed and execute
        
        Returns:
            Observation from tool execution or None
        """
        path_str = best_path['path_str']
        
        # Check if we need tools
        tools = self.registry.get_tool_descriptions()
        tools_list = "\n".join([f"- {n}: {d}" for n, d in tools.items()])
        
        prompt = f"""Query: {query}

Best reasoning path selected:
{path_str}

Available tools:
{tools_list}

Do we need to use any tools to execute this solution?

Respond with ONLY valid JSON:
{{
    "needs_tool": true/false,
    "tool_name": "tool_name" or null,
    "parameters": {{}} or null,
    "reason": "why we need/don't need tool"
}}

JSON:"""
        
        response = self.model.generate(prompt, max_tokens=200, temperature=0.1)
        
        try:
            # Parse decision
            response = response.strip()
            if "```" in response:
                parts = response.split("```")
                for part in parts:
                    if "{" in part:
                        response = part.replace("json", "").strip()
                        break
            
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                decision = json.loads(response[start:end])
                
                if decision.get('needs_tool'):
                    tool_name = decision.get('tool_name')
                    params = decision.get('parameters', {})
                    
                    logger.info(f"✓ Executing tool: {tool_name}")
                    result = self.registry.execute_tool(tool_name, **params)
                    
                    if result.success:
                        # Format observation
                        if isinstance(result.data, list):
                            obs = "\n".join([
                                f"{i+1}. {item.get('title', 'N/A')}: {item.get('snippet', 'N/A')[:100]}"
                                for i, item in enumerate(result.data[:5])
                            ])
                        else:
                            obs = str(result.data)
                        
                        logger.info(f"  Tool succeeded: {len(obs)} chars")
                        return obs
                    else:
                        logger.error(f"  Tool failed: {result.error}")
                        return f"Error: {result.error}"
                else:
                    logger.info("✓ No tool execution needed")
                    return None
                    
        except Exception as e:
            logger.warning(f"Failed to parse tool decision: {e}")
        
        return None
    
    def _final_answer(self, query: str, best_path: Dict, observation: Optional[str]) -> str:
        """
        Generate final answer based on best path
        
        Args:
            query: Original query
            best_path: Selected best path
            observation: Optional tool observation
            
        Returns:
            Final answer
        """
        path_str = best_path['path_str']
        evaluation = best_path['evaluation']
        score = best_path['score']
        
        if observation:
            prompt = f"""Question: {query}

Best reasoning approach (score: {score}/10):
{path_str}

Why this approach is best:
{evaluation}

Additional information gathered:
{observation}

Based on the selected approach and information gathered, provide a comprehensive final answer.

Answer:"""
        else:
            prompt = f"""Question: {query}

Best reasoning approach (score: {score}/10):
{path_str}

Why this approach is best:
{evaluation}

Based on this approach, provide a comprehensive final answer.

Answer:"""
        
        response = self.model.generate(prompt, max_tokens=600, temperature=0.5)
        logger.info(f"Generated final answer: {len(response)} characters")
        
        return response.strip()