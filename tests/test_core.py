import pandas as pd
import numpy as np
import pytest

from himcm.core import calculate_sustainability_scores, compute_env_condition_metric


def make_sample_df():
    return pd.DataFrame([
        {'City':'A','Times_Hosted':1,'Last_Hosted_Year':2010,'Stadium_Type':'Dome','Avg_Feb_Temp_F':40,'Alltransit_Score':80,'Renewable_Energy_Pct':60,'Waste_Diversion_Pct':50,'Green_Legacy_Projects':2,'Carbon_Offset_Programs':1,'Stadium_leed_cert':'Gold','Water_Score':70,'Air_ug_m3':12,'Carbon_Emissions':2.5},
        {'City':'B','Times_Hosted':0,'Last_Hosted_Year':0,'Stadium_Type':'Open','Avg_Feb_Temp_F':55,'Alltransit_Score':60,'Renewable_Energy_Pct':20,'Waste_Diversion_Pct':30,'Green_Legacy_Projects':0,'Carbon_Offset_Programs':0,'Stadium_leed_cert':'Certified','Water_Score':50,'Air_ug_m3':25,'Carbon_Emissions':5.0},
        {'City':'C','Times_Hosted':2,'Last_Hosted_Year':2022,'Stadium_Type':'Retractable','Avg_Feb_Temp_F':35,'Alltransit_Score':90,'Renewable_Energy_Pct':80,'Waste_Diversion_Pct':70,'Green_Legacy_Projects':5,'Carbon_Offset_Programs':3,'Stadium_leed_cert':'Platinum','Water_Score':80,'Air_ug_m3':8,'Carbon_Emissions':1.2},
    ])


def test_calculate_scores_basic():
    df = make_sample_df()
    out = calculate_sustainability_scores(df)
    assert 'Raw_Score' in out.columns
    assert 'Sustainability_Z' in out.columns
    assert 'Sustainability_Z_Scaled' in out.columns
    # Check that scaled z has mean approx 50
    mean_scaled = out['Sustainability_Z_Scaled'].mean()
    assert pytest.approx(mean_scaled, rel=1e-1) == 50


def test_env_metric_components():
    df = make_sample_df()
    # Test env metric on first row
    row = df.iloc[0]
    val = compute_env_condition_metric(df, row)
    assert isinstance(val, float)
    assert 0 <= val <= 100


def test_missing_columns_behavior():
    df = pd.DataFrame([{'City':'X'}])
    out = calculate_sustainability_scores(df)
    # With no data, Raw_Score should be numeric and Z should be defined
    assert 'Raw_Score' in out.columns
    assert out['Raw_Score'].dtype.kind in 'fi'

