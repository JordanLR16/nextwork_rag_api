import { ADD_API_KEY, postJson } from "./client";

export function askKnowledgeBase(question, nResults = 3) {
  return postJson("/query", { q: question, n_results: nResults });
}

export function addRecipeKnowledge(text) {
  const extraHeaders = ADD_API_KEY ? { "X-API-Key": ADD_API_KEY } : {};
  return postJson("/add", { text }, extraHeaders);
}
