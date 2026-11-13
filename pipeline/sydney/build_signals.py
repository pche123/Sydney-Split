"""Build ~45 plain-language Census signals per SA2 (or SA1) from a 2021 GCP DataPack.

Usage: python build_signals.py <datapack_dir> <level SA1|SA2> <out.csv>
Ancestry, language and religion are deliberately left out of this "fun lines" set.
"""
import sys, glob, os
import pandas as pd
import numpy as np

src, level, out = sys.argv[1], sys.argv[2], sys.argv[3]
key = f"{level}_CODE_2021"


def load(table):
    files = sorted(glob.glob(os.path.join(src, f"2021Census_{table}*_NSW_{level}.csv")))
    df = None
    for f in files:
        d = pd.read_csv(f, dtype={key: str}).set_index(key)
        df = d if df is None else df.join(d, how="outer", rsuffix="_dup")
    return df


G = {t: load(t) for t in ["G01", "G02", "G15", "G23", "G34", "G35", "G36", "G37",
                          "G41", "G44", "G49", "G54", "G60", "G62"]}


def share(t, num, den):
    d = G[t]
    n = d[num].sum(axis=1) if isinstance(num, list) else d[num]
    return n / d[den].replace(0, np.nan)


S = {}  # name -> (series, plain-English label for "higher" side)
g01 = G["G01"]
pop = g01["Tot_P_P"]
S["kids_0_14"] = share("G01", ["Age_0_4_yr_P", "Age_5_14_yr_P"], "Tot_P_P")
S["young_adults_20_34"] = share("G01", ["Age_20_24_yr_P", "Age_25_34_yr_P"], "Tot_P_P")
S["retirees_65plus"] = share("G01", ["Age_65_74_yr_P", "Age_75_84_yr_P", "Age_85ov_P"], "Tot_P_P")
S["year12_finished"] = g01["High_yr_schl_comp_Yr_12_eq_P"] / (g01[[c for c in g01.columns if c.startswith("High_yr_schl_comp_") and c.endswith("_P")]].sum(axis=1)).replace(0, np.nan)
for c in ["Median_age_persons", "Median_mortgage_repay_monthly", "Median_rent_weekly",
          "Median_tot_hhd_inc_weekly", "Average_num_psns_per_bedroom", "Average_household_size"]:
    S[c.lower()] = G["G02"][c].replace(0, np.nan)

g15 = G["G15"]
S["private_high_school"] = (g15["Secondary_Catholic_P"] + g15["Secondary_Other_non_Govt_P"]) / g15["Secondary_Tot_Secondary_P"].replace(0, np.nan)
S["uni_students"] = g15["Tert_Uni_other_high_edu_Tot_P"] / pop
S["tafe_students"] = g15["Tert_Voc_edu_Tot_P"] / pop
S["volunteers"] = share("G23", "P_Tot_Volunteer", "P_Tot_Tot")

S["no_car"] = share("G34", "Num_MVs_per_dweling_0_MVs", "Total_dwelings")
S["three_plus_cars"] = share("G34", ["Num_MVs_per_dweling_3_MVs", "Num_MVs_per_dweling_4mo_MVs"], "Total_dwelings")

g35 = G["G35"]
S["living_alone"] = g35["Num_Psns_UR_1_Total"] / g35["Total_Total"].replace(0, np.nan)
S["share_houses"] = (g35["Total_NonFamHhold"] - g35["Num_Psns_UR_1_NonFamHhold"]) / g35["Total_Total"].replace(0, np.nan)
S["big_households_6plus"] = g35["Num_Psns_UR_6mo_Total"] / g35["Total_Total"].replace(0, np.nan)

g36 = G["G36"]
S["detached_houses"] = share("G36", "OPDs_Separate_house_Dwellings", "OPDs_Tot_OPDs_Dwellings")
S["townhouses"] = share("G36", "OPDs_SD_r_t_h_th_Tot_Dwgs", "OPDs_Tot_OPDs_Dwellings")
S["apartments"] = share("G36", "OPDs_Flt_apart_Tot_Dwgs", "OPDs_Tot_OPDs_Dwellings")
S["high_rise_9plus"] = share("G36", "OPDs_F_ap_I_9_m_sty_blk_Ds", "OPDs_Tot_OPDs_Dwellings")
S["empty_dwellings"] = share("G36", "Unoccupied_PDs_Dwgs", "Total_PDs_Dwellings")

S["owned_outright"] = share("G37", "O_OR_Total", "Total_Total")
S["mortgaged"] = share("G37", "O_MTG_Total", "Total_Total")
S["renting_private"] = share("G37", "R_RE_Agt_Total", "Total_Total")
S["social_housing"] = share("G37", ["R_ST_h_auth_Total", "R_Com_Hp_Total"], "Total_Total")

g41 = G["G41"]
S["four_plus_bedrooms"] = (g41["Total_NofB_4"] + g41["Total_NofB_5"] + g41["Total_NofB_6_or_m"]) / g41["Total_Total"].replace(0, np.nan)

g44 = G["G44"]
S["moved_in_last_year"] = (g44["Difnt_Usl_add_1_yr_ago_Tot_P"]) / g44["Tot_P"].replace(0, np.nan)
S["arrived_from_overseas_last_year"] = g44["Difnt_Usl_add_1_yr_ago_OS_P"] / g44["Tot_P"].replace(0, np.nan)

g49 = G["G49"]
S["university_degree"] = (g49["P_PGrad_Deg_Total"] + g49["P_GradDip_and_GradCert_Total"] + g49["P_BachDeg_Total"]) / pop
S["trade_certificate"] = g49["P_Cert_III_IV_Total"] / pop

g54 = G["G54"]
for c, n in [("P_Constru_Tot", "works_construction"), ("P_Manufact_Tot", "works_manufacturing"),
             ("P_HlthCare_SocAs_Tot", "works_health_care"), ("P_Fin_Insur_Tot", "works_finance"),
             ("P_Pro_scien_tec_Tot", "works_professional_services"), ("P_Accom_food_Tot", "works_hospitality"),
             ("P_Trans_post_wrehsg_Tot", "works_transport_logistics"), ("P_RetTde_Tot", "works_retail"),
             ("P_Info_media_teleco_Tot", "works_media_tech"), ("P_Educ_trng_Tot", "works_education")]:
    S[n] = share("G54", c, "P_Tot_Tot")

for c, n in [("P_Tot_Managers", "managers"), ("P_Tot_Professionals", "professionals"),
             ("P_Tot_TechnicTrades_W", "tradies"), ("P_Tot_Labourers", "labourers"),
             ("P_Tot_Mach_oper_drivers", "drivers_operators"), ("P_Tot_CommunPersnlSvc_W", "care_service_workers")]:
    S[n] = share("G60", c, "P_Tot_Tot")

g62 = G["G62"]
workers = (g62["Tot_P"] - g62["Did_not_go_to_work_P"] - g62["Method_travel_to_work_ns_P"]).replace(0, np.nan)
S["train_commute"] = (g62["One_method_Train_P"] + g62["Two_methods_Train_Tot_P"] + g62["Three_meth_Tr_2_oth_meth_P"]) / workers
S["bus_commute"] = (g62["One_method_Bus_P"] + g62["Two_methods_Bus_Tot_P"]) / workers
# ferry too sparse
_ferry = (g62["One_method_Ferry_P"] + g62["Two_methods_Train_Ferry_P"] + g62["Two_methods_Bus_Ferry_P"]) / workers
S["drive_to_work"] = g62["One_method_Car_as_driver_P"] / workers
S["walk_to_work"] = g62["One_method_Walked_only_P"] / workers
S["cycle_to_work"] = g62["One_method_Bicycle_P"] / workers
S["work_from_home"] = g62["Worked_home_P"] / workers
S["ute_truck_commute"] = g62["One_method_Truck_P"] / workers

df = pd.DataFrame(S)
ratio_cols = [c for c in df.columns if not c.startswith(("median_", "average_"))]
df[ratio_cols] = df[ratio_cols].clip(0, 1)
df.insert(0, "population", pop)
df.index.name = key
df.to_csv(out)
print(df.shape, "signals:", len(S))
print(df.describe().T[["mean", "min", "max"]].round(3).to_string())
