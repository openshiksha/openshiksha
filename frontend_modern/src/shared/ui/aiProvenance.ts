/**
 * True when the LLM cascade fell back to the deterministic, data-derived stub.
 * Every AI serializer carries `model_used`; `'stub'` is the no-LLM sentinel.
 */
export const isAIStub = (modelUsed: string | null | undefined): boolean => modelUsed === 'stub';
