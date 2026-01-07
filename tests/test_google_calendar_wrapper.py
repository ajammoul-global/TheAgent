def test_google_calendar_wrapper_importable():
    import importlib

    mod = importlib.import_module("tools.Google_calender")

    # The wrapper should expose the aliases (if the underlying modules exist)
    assert hasattr(mod, "GoogleCalendarTool")
    assert hasattr(mod, "GoogleCalendarCreateTool")
    assert hasattr(mod, "GoogleCalendarListTool")


def test_tool_registry_no_duplicate_calendar_tools():
    from infra.tool_registry import ToolRegistry

    registry = ToolRegistry()
    tools = registry.list_tools()

    # Each calendar tool should appear at most once
    assert tools.count("google_calendar_create") <= 1
    assert tools.count("google_calendar_list") <= 1
