import { getJson, postJson } from "./client";

export const pantryApi = {
  async listIngredients() {
    const data = await getJson("/pantry");
    return data.items;
  },
  addIngredient(item) {
    return postJson("/pantry", item);
  },
};
