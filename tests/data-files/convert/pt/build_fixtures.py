"""Cut the pt 2017-2019 test fixtures, choosing rows that exercise each mechanism.

Run against extracted copies of the real archives; see README.md for what each cut is for.
"""

import os
import shutil
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

SRC = "/u/haithcoatj/ftw/tmp/pt-recon"
OUT = f"{SRC}/fixtures"
shutil.rmtree(OUT, ignore_errors=True)


def read(year, stem, **kw):
    return gpd.read_file(f"{SRC}/extracted.{year}/{stem}.shp", **kw)


def write(year, stem, gdf):
    d = f"{OUT}/{year}"
    os.makedirs(d, exist_ok=True)
    gdf.to_file(f"{d}/{stem}.shp", engine="pyogrio", encoding="UTF-8")
    with open(f"{d}/{stem}.cpg", "w") as fh:
        fh.write("UTF-8")
    print(
        f"  {year}/{stem}.shp  {len(gdf):>4} rows  crs={gdf.crs.to_string() if gdf.crs else None}"
    )


def head(year, stem, n):
    write(year, stem, read(year, stem, rows=n))


print("2017")
for stem, n in [
    ("Ocupacoes_solo_AML", 20),
    ("Ocupacoes_solo_Alentejo", 100),
    ("Ocupacoes_solo_Algarve", 20),
    ("Ocupacoes_solo_Centro_N", 20),
    ("Ocupacoes_solo_Centro_S", 20),
    ("Ocupacoes_solo_Norte_S", 20),
    ("ocupacoes_solo_norte_n1", 100),
    ("ocupacoes_solo_norte_n2", 20),
    ("Parcelas_Alentejo", 5),
]:
    head(2017, stem, n)

# 2017 islands: keep rows whose PAR_NUM repeats, so the synthetic id path is exercised
# on exactly the condition that forced it (PAR_NUM is not unique).
for stem, n in [("Ocupacoes_solo_RAA", 100), ("Ocupacoes_solo_RAM", 60)]:
    g = read(2017, stem)
    vc = g["PAR_NUM"].value_counts()
    repeated = vc[vc > 1].index[:12]
    keep = pd.concat([g[g["PAR_NUM"].isin(repeated)], g[~g["PAR_NUM"].isin(repeated)].head(n)])
    keep = keep.head(n).reset_index(drop=True)
    dup = int(keep["PAR_NUM"].duplicated().sum())
    assert dup > 0, f"{stem}: fixture must repeat a PAR_NUM, got none"
    print(f"    ({stem}: {dup} repeated PAR_NUM in fixture)")
    write(2017, stem, keep)

print("2018")
for stem, n in [
    ("Ocupacoes_solo_AML", 20),
    ("Ocupacoes_solo_Alentejo", 20),
    ("Ocupacoes_solo_Algarve", 20),
    ("Ocupacoes_solo_Centro_N", 20),
    ("Ocupacoes_solo_Centro_S", 20),
    ("Ocupacoes_solo_RAA", 30),
    ("Ocupacoes_solo_RAM", 20),
    ("Parcelas_AML", 5),
]:
    head(2018, stem, n)

# the duplicate pair: 30 ids in both files, plus rows unique to each
nn = read(2018, "Ocupacoes_solo_Norte_N")
ns = read(2018, "Ocupacoes_solo_Norte_S")
# every id the two files share, so the "unique" half of each fixture can exclude all of
# them and the fixture overlap is exactly the 30 we pick
overlap = np.intersect1d(nn["OSA_ID"].values, ns["OSA_ID"].values)
shared = overlap[:30]
nn_keep = pd.concat(
    [nn[nn["OSA_ID"].isin(shared)], nn[~nn["OSA_ID"].isin(overlap)].head(70)]
).reset_index(drop=True)
ns_keep = pd.concat(
    [ns[ns["OSA_ID"].isin(shared)], ns[~ns["OSA_ID"].isin(overlap)].head(70)]
).reset_index(drop=True)
assert len(np.intersect1d(nn_keep["OSA_ID"], ns_keep["OSA_ID"])) == 30
print(f"    (Norte_N/Norte_S fixtures share {len(shared)} OSA_IDs)")
write(2018, "Ocupacoes_solo_Norte_N", nn_keep)
write(2018, "Ocupacoes_solo_Norte_S", ns_keep)

# the '?' names, the non-contiguous lowercase c1..c7,c9, and EPSG:3763, all in one file
n1 = read(2018, "ocupacoes.solo.Norte_N1.2018jun10")
q = n1[n1["c1"].astype("string").str.contains(r"\?", regex=True, na=False)]
picked = q.groupby("c1", dropna=True).head(2)
keep = pd.concat([picked, n1[~n1.index.isin(picked.index)].head(40)]).reset_index(drop=True)
present = sorted(keep["c1"].dropna().unique())
print(f"    (Norte_N1 fixture carries {sum('?' in v for v in present)} distinct '?' names)")
write(2018, "ocupacoes.solo.Norte_N1.2018jun10", keep)

print("2019")
for stem, n in [
    ("Ocupacoes_solo_AML", 20),
    ("Ocupacoes_solo_Alentejo", 20),
    ("Ocupacoes_solo_Algarve", 20),
    ("Ocupacoes_solo_Centro_N", 20),
    ("Ocupacoes_solo_Centro_S", 20),
    ("Ocupacoes_solo_Norte_S", 20),
    ("Ocupacoes_solo_RAA", 100),
    ("Ocupacoes_solo_RAM", 20),
    ("ocupacoes_solo_n_1", 100),
    ("ocupacoes_solo_n_2", 20),
    ("Parcelas_AML", 5),
]:
    head(2019, stem, n)
# the junk the member list must simply never name
open(f"{OUT}/2019/osas_az_ocidental.qpj", "w").write('GEOGCS["GCS_WGS_1984"]')
open(f"{OUT}/2019/Ocupacoes_solo_AML.shp.EPC0444.340.5752.sr.lock", "w").write("")

for year in (2017, 2018, 2019):
    z = f"{OUT}/{year}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in sorted(os.listdir(f"{OUT}/{year}")):
            zf.write(f"{OUT}/{year}/{f}", f)
    print(f"{z}: {os.path.getsize(z) / 1024 / 1024:.2f} MB")
