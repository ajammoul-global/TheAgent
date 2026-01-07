def test_memory_package_exports():
    import memory

    assert hasattr(memory, "ConversationStore")
    assert hasattr(memory, "ContextManager")
    assert hasattr(memory, "PreferenceEngine")
