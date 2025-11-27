from services.clusterer import cluster_pois_kmeans

def test_clusterer_deterministic():
    pois = [
        {"id":"p1","name":"A","lat":40.44,"lon":-80.00,"rating":4.5,"review_count":100,"must_go":True},
        {"id":"p2","name":"B","lat":40.441,"lon":-80.001,"rating":4.2,"review_count":80,"must_go":True},
        {"id":"p3","name":"C","lat":40.442,"lon":-80.002,"rating":4.1,"review_count":50,"must_go":False},
        {"id":"p4","name":"D","lat":40.455,"lon":-79.95,"rating":4.6,"review_count":200,"must_go":False},
        {"id":"p5","name":"E","lat":40.456,"lon":-79.951,"rating":4.3,"review_count":120,"must_go":False},
        {"id":"p6","name":"F","lat":40.457,"lon":-79.952,"rating":4.0,"review_count":60,"must_go":False},
        {"id":"p7","name":"G","lat":40.47,"lon":-79.93,"rating":4.8,"review_count":500,"must_go":True},
        {"id":"p8","name":"H","lat":40.471,"lon":-79.931,"rating":4.7,"review_count":400,"must_go":True},
    ]
    res1 = cluster_pois_kmeans(pois, k=3, random_state=42)
    res2 = cluster_pois_kmeans(pois, k=3, random_state=42)

    assert [c["poi_ids"] for c in res1["clusters"]] == [c["poi_ids"] for c in res2["clusters"]]
    assert len(res1["clusters"]) == 3
    assert sum(len(c["poi_ids"]) for c in res1["clusters"]) == len(pois)

