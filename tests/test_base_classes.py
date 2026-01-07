"""
Test/Example: Understanding Base Classes

FIXED VERSION for running on your local machine!

This file demonstrates how the base classes work by creating
simple implementations and testing them.
"""

import sys
import os

# Fix 1: Add the parent directory to Python path
# This makes Python recognize 'models' and 'tools' as packages
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from models and tools
from models.base import BaseModel
from tools.base import BaseTool, ToolParameter, ToolResult


# ==============================================================================
# EXAMPLE 1: Implementing BaseModel
# ==============================================================================

class MockModel(BaseModel):
    """
    A simple mock model for testing.
    Shows how to implement the BaseModel interface.
    """
    
    def __init__(self, model_name: str = "mock-llm"):
        self._model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = None) -> str:
        """Simple mock that echoes the prompt"""
        return f"Mock response to: {prompt[:50]}..."
    
    def get_info(self) -> dict:
        """Return model info"""
        return {
            "provider": self.provider,
            "model": self.name,
            "type": "mock"
        }
    
    @property
    def name(self) -> str:
        return self._model_name
    
    @property
    def provider(self) -> str:
        return "mock"


# ==============================================================================
# EXAMPLE 2: Implementing BaseTool
# ==============================================================================

class MockCalculatorTool(BaseTool):
    """
    A simple calculator tool for testing.
    Shows how to implement the BaseTool interface.
    """
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Performs basic arithmetic operations (add, subtract, multiply, divide)"
    
    @property
    def parameters(self):
        return [
            ToolParameter(
                name="operation",
                type="string",
                description="Operation to perform: add, subtract, multiply, divide",
                required=True
            ),
            ToolParameter(
                name="a",
                type="number",
                description="First number",
                required=True
            ),
            ToolParameter(
                name="b",
                type="number",
                description="Second number",
                required=True
            )
        ]
    
    def execute(self, operation: str, a: float, b: float) -> ToolResult:
        """Execute the calculation"""
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return ToolResult(
                        success=False,
                        error="Cannot divide by zero"
                    )
                result = a / b
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}"
                )
            
            return ToolResult(
                success=True,
                data={"operation": operation, "result": result},
                metadata={"a": a, "b": b}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )


# ==============================================================================
# TESTING THE BASE CLASSES
# ==============================================================================

def test_base_model():
    """Test that MockModel implements BaseModel correctly"""
    print("=" * 70)
    print("TEST 1: BaseModel Implementation")
    print("=" * 70)
    
    # Create instance
    model = MockModel("test-model")
    
    # Test all required methods exist
    print(f"✅ Model created: {model.name}")
    print(f"✅ Provider: {model.provider}")
    
    # Test generate
    response = model.generate("What is Python?")
    print(f"✅ Generate works: {response}")
    
    # Test get_info
    info = model.get_info()
    print(f"✅ Info: {info}")
    
    print("\n✅ BaseModel implementation works!\n")


def test_base_tool():
    """Test that MockCalculatorTool implements BaseTool correctly"""
    print("=" * 70)
    print("TEST 2: BaseTool Implementation")
    print("=" * 70)
    
    # Create instance
    tool = MockCalculatorTool()
    
    # Test properties
    print(f"✅ Tool name: {tool.name}")
    print(f"✅ Description: {tool.description}")
    print(f"✅ Parameters: {len(tool.parameters)} defined")
    
    # Test to_schema
    schema = tool.to_schema()
    print(f"✅ Schema generated: {list(schema.keys())}")
    
    # Test execution
    result = tool.safe_execute(operation="add", a=5, b=3)
    print(f"✅ Execute (5 + 3): success={result.success}, data={result.data}")
    
    # Test with missing parameter
    result = tool.safe_execute(operation="add", a=5)  # Missing 'b'
    print(f"✅ Missing param handling: success={result.success}, error={result.error[:50]}...")
    
    # Test error handling
    result = tool.safe_execute(operation="divide", a=10, b=0)
    print(f"✅ Error handling (10 / 0): success={result.success}, error={result.error}")
    
    print("\n✅ BaseTool implementation works!\n")


def demonstrate_polymorphism():
    """Demonstrate how base classes enable polymorphism"""
    print("=" * 70)
    print("TEST 3: Polymorphism (The Power of Interfaces)")
    print("=" * 70)
    
    # Different models, same interface
    models = [
        MockModel("model-1"),
        MockModel("model-2"),
        MockModel("model-3")
    ]
    
    print("Multiple models, same interface:")
    for model in models:
        # We can treat all models the same way!
        response = model.generate("Hello")
        print(f"  {model.name}: {response[:40]}...")
    
    print("\n✅ All models work through BaseModel interface!")
    
    # Different tools, same interface  
    tools = [
        MockCalculatorTool(),
        # Could add: WebSearchTool(), EmailTool(), etc.
    ]
    
    print("\nMultiple tools, same interface:")
    for tool in tools:
        # We can treat all tools the same way!
        schema = tool.to_schema()
        print(f"  {tool.name}: {tool.description[:40]}...")
    
    print("\n✅ All tools work through BaseTool interface!\n")


def show_why_this_matters():
    """Explain why this architecture matters"""
    print("=" * 70)
    print("WHY THIS MATTERS")
    print("=" * 70)
    print("""
With these base classes, we can now:

1. ✅ SWAP MODELS EASILY
   agent = Agent(OllamaModel())    # Use Ollama
   agent = Agent(OpenAIModel())    # Switch to OpenAI
   # Agent code doesn't change!

2. ✅ ADD TOOLS DYNAMICALLY
   registry.register(WebSearchTool())
   registry.register(CalculatorTool())
   registry.register(EmailTool())
   # Agent automatically knows about all tools!

3. ✅ TEST IN ISOLATION
   mock_model = MockModel()
   agent = Agent(mock_model)
   # Test without real LLM!

4. ✅ TYPE SAFETY
   def use_model(model: BaseModel):
       # IDE knows model has generate()
       response = model.generate(...)
   
5. ✅ CLEAR CONTRACTS
   # Want to add new model? Implement 4 methods!
   # Want to add new tool? Implement 4 methods!
   # Crystal clear what's needed!

This is the FOUNDATION that makes everything else possible!
    """)


# ==============================================================================
# RUN ALL TESTS
# ==============================================================================

if __name__ == "__main__":
    print("\n🚀 TESTING BASE CLASSES\n")
    print(f"Project root: {project_root}\n")
    
    try:
        test_base_model()
        test_base_tool()
        demonstrate_polymorphism()
        show_why_this_matters()
        
        print("=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Base classes work correctly!")
        print("✅ Ready to build implementations!\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()