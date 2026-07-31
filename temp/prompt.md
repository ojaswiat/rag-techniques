Using superpowers, I want you to overhaul how the LLMclient is initiated.
**Ignore if this is what it already is**

1. Create a class to intantiate any provider with the model.
    - get_client function returns a client with the provider and model correctly instantiated so that whenever that client is called, it works as expected.
    - The individual code for instantiation will remain in seprate files e.g.: groq_client.py, nim_client.py.
    - The one and only job of this class is to return me working client. That's it.
    - the get_client function returns llm_client by using the files groq_client.py or nim_client.py.
2. I originally wanted this change.
3. Only implementing this should break the existing behaviour.
4. Make sure you use this new Class to instantiate a client wherever it is being used with proper parameters.

If this is what is happening already, leave it. NO NEED TO TEST groq client by calling the API now (limit exhausted), just make sure it works doing a static check.
