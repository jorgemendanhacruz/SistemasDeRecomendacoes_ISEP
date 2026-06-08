import pandas as pd
from src.models.cbf_model import get_recommendations
from src.fastapi_recommender.cf_model import get_cf_recommendations, get_user_based_cf_recommendations


def _short(name, limit=45):
    return name if len(name) <= limit else name[:limit].rstrip() + "..."


def mixed_hybrid_recommender(
    user_id,
    ratings_df,
    products_df,
    similarity_matrix,
    user_item_matrix,
    item_similarity_df,
    user_similarity_df,
    top_pool,
    avg_ratings,
    n_top=3,
    n_cbf=3,
    n_cf=4,
):
    user_ratings_df = ratings_df[ratings_df["user_id"] == user_id]
    num_ratings = len(user_ratings_df)
    seen = set()
    results = []

    product_index_map = pd.Series(products_df.index, index=products_df["product_id"]).to_dict()

    def _find_cbf_source(rec_id, rated_dict):
        if rec_id not in product_index_map:
            return None
        rec_idx = product_index_map[rec_id]
        best_pid, best_score = None, -1.0
        for pid in rated_dict:
            if pid not in product_index_map:
                continue
            score = float(similarity_matrix[rec_idx, product_index_map[pid]])
            if score > best_score:
                best_score, best_pid = score, pid
        return best_pid

    def _product_row(product_id):
        row = products_df[products_df["product_id"] == product_id]
        if row.empty:
            return None
        r = row.iloc[0]
        avg = avg_ratings.get(product_id, float("nan"))
        return {
            "product_id": product_id,
            "product_name": r["product_name"],
            "category": r["category"].split("|")[0],
            "discounted_price": r["discounted_price"],
            "avg_rating": round(avg, 2) if avg == avg else None,
        }

    def _take_from_top(n, source_label, explanation_fn):
        count = 0
        for _, row in top_pool.iterrows():
            if count >= n:
                break
            if row["product_id"] in seen:
                continue
            seen.add(row["product_id"])
            results.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"].split("|")[0],
                "discounted_price": row["discounted_price"],
                "avg_rating": round(row["avg_rating"], 2),
                "source": source_label,
                "explanation": explanation_fn(row),
            })
            count += 1

    # Slice 1: Non-personalized top-rated
    _take_from_top(
        n_top,
        source_label="non_personalized",
        explanation_fn=lambda r: f"Top rated product (avg {r['avg_rating']:.1f})",
    )

    # Slice 2: Content-based filtering
    if num_ratings >= 1:
        rated = dict(zip(user_ratings_df["product_id"], user_ratings_df["rating"]))
        cbf_ids = get_recommendations(rated, similarity_matrix, products_df, n_cbf * 4)

        count = 0
        for rec_id in cbf_ids:
            if count >= n_cbf:
                break
            if rec_id in seen:
                continue
            info = _product_row(rec_id)
            if info is None:
                continue
            seen.add(rec_id)

            source_pid = _find_cbf_source(rec_id, rated)
            if source_pid:
                name_row = products_df[products_df["product_id"] == source_pid]["product_name"].values
                source_name = _short(name_row[0]) if len(name_row) > 0 else "a product you rated"
            else:
                source_name = "a product you rated"

            info["source"] = "content_based"
            info["explanation"] = f'Because you liked "{source_name}"'
            results.append(info)
            count += 1

        if count < n_cbf:
            _take_from_top(
                n_cbf - count,
                source_label="non_personalized_fallback",
                explanation_fn=lambda r: f"Top rated product (avg {r['avg_rating']:.1f})",
            )
    else:
        _take_from_top(
            n_cbf,
            source_label="non_personalized_fallback",
            explanation_fn=lambda r: "Popular pick — rate products to get personalised suggestions",
        )

    # Slice 3: Collaborative filtering
    if num_ratings > 1:
        cf_ids = get_user_based_cf_recommendations(
            user_id, user_item_matrix, user_similarity_df, n=n_cf * 4
        )
        cf_source = "user_based_cf"
        if not cf_ids:
            cf_ids = get_cf_recommendations(
                user_id, user_item_matrix, item_similarity_df, n=n_cf * 4
            )
            cf_source = "item_based_cf"

        count = 0
        for rec_id in cf_ids:
            if count >= n_cf:
                break
            if rec_id in seen:
                continue
            info = _product_row(rec_id)
            if info is None:
                continue
            seen.add(rec_id)
            info["source"] = cf_source
            info["explanation"] = "Users with similar taste also liked this"
            results.append(info)
            count += 1

        if count < n_cf:
            _take_from_top(
                n_cf - count,
                source_label="non_personalized_fallback",
                explanation_fn=lambda r: f"Top rated product (avg {r['avg_rating']:.1f})",
            )
    else:
        msg = (
            "Rate 1 more product to unlock personalised CF recommendations"
            if num_ratings == 1
            else "Rate some products to unlock personalised recommendations"
        )
        _take_from_top(
            n_cf,
            source_label="non_personalized_fallback",
            explanation_fn=lambda r: msg,
        )

    return results
