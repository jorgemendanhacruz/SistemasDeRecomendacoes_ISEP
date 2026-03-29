import pandas as pd


#--------- Recommendations ---------------------------#


def get_nearest_products(product_id, similarity_matrix, df, k):
    product_index_map = pd.Series(
        df.index,
        index=df["product_id"]
    ).to_dict()

    if product_id not in product_index_map:
        return {}

    index = product_index_map[product_id]

    similarity_scores = list(enumerate(similarity_matrix[index]))

    similarity_scores = sorted(
        similarity_scores,
        key=lambda x: x[1],
        reverse=True
    )

    top_products = similarity_scores[1:k+1]

    k_nearest = {
        df.iloc[i]["product_id"]: score
        for i, score in top_products
    }

    return k_nearest


def get_recommendations(rated_products, similarity_matrix,df,n):

    candidates = {}

    for p, r in rated_products.items():

        k_nearest = get_nearest_products(p,similarity_matrix,df,n*2)

        for product, cos_sim in k_nearest.items():
            if product in rated_products:
                continue
            if product in candidates:
                candidates[product] += float(cos_sim)
            else:
                candidates[product] = float(cos_sim) * r
    
    recommendations = [
        product_id 
        for product_id, _ in sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:n]
    ]

    return recommendations