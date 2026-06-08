import pandas as pd


def get_cf_recommendations(user_id, user_item_matrix, item_similarity_df, n=5):
    if user_id not in user_item_matrix.index:
        return []

    user_ratings = user_item_matrix.loc[user_id].dropna()
    scores = {}

    for product_id, rating in user_ratings.items():
        if product_id not in item_similarity_df.columns:
            continue
        similar_items = item_similarity_df[product_id]
        for sim_product, sim_score in similar_items.items():
            if sim_product == product_id:
                continue
            scores[sim_product] = scores.get(sim_product, 0) + sim_score * rating

    scores = {k: v for k, v in scores.items() if k not in user_ratings.index}
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [item for item, _ in ranked[:n]]


def get_user_based_cf_recommendations(user_id, user_item_matrix, user_similarity_df, n=5, k_users=10):
    if user_id not in user_item_matrix.index:
        return []

    sim_users = (
        user_similarity_df[user_id]
        .drop(index=user_id)
        .sort_values(ascending=False)
        .head(k_users)
    )

    already_rated = set(user_item_matrix.loc[user_id].dropna().index)
    scores = {}

    for sim_user_id, sim_score in sim_users.items():
        sim_user_ratings = user_item_matrix.loc[sim_user_id].dropna()
        for product_id, rating in sim_user_ratings.items():
            if product_id in already_rated:
                continue
            scores[product_id] = scores.get(product_id, 0) + sim_score * rating

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [product_id for product_id, _ in ranked[:n]]
