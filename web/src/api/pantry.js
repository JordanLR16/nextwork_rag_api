import { ADD_API_KEY, getJson, postJson } from "./client";

export const pantryApi = {
  async listIngredients() {
    const data = await getJson("/pantry");
    return data.items;
  },
  addIngredient(item) {
    const headers = ADD_API_KEY ? { "X-API-Key": ADD_API_KEY } : {};
    return postJson("/pantry", item, headers);
  },
};
