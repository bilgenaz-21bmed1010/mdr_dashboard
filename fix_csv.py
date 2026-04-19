import pandas as pd

df = pd.read_csv("data/incidents.csv")
df["ciddiyet"] = df["ciddiyet"].replace({
    "Acil (Halk Sağlığı Tehdidi)": "Serious (Public Health Threat)",
    "Ciddi (Ölüm/Beklenmedik Bozulma)": "Serious (Death/Unanticipated)",
    "Ciddi (Beklenen Bozulma)": "Serious (Anticipated Deterioration)",
})
df["durum"] = df["durum"].replace({
    "Açık": "Open", "Kapalı": "Closed", "Geçmiş": "Overdue",
})
df.to_csv("data/incidents.csv", index=False)

df2 = pd.read_csv("data/fsca.csv")
df2["durum"] = df2["durum"].replace({"Aktif": "Active", "Kapalı": "Closed"})
df2["mevcut_asama"] = df2["mevcut_asama"].replace({
    "Tespit": "Detection", "Değerlendirme": "Assessment",
    "Bildirim": "Notification", "Uygulama": "Implementation", "Kapanış": "Closure",
})
df2.to_csv("data/fsca.csv", index=False)

df3 = pd.read_csv("data/devices.csv")
df3["durum"] = df3["durum"].replace({
    "Aktif": "Active", "Pasif": "Inactive", "İnceleme": "Under Review",
})
df3.to_csv("data/devices.csv", index=False)
print("Done")