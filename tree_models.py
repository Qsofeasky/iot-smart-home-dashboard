"""
Auto-generated decision tree prediction functions.
NO external libraries needed (no sklearn, no joblib, no ONNX, no TFLite).
Generated from trained models -- Light Tree Accuracy: 0.967, Aircond Tree MAE: 0.41
"""

def predict_light(features):
    # features = dict with keys: ['temperature', 'brightness', 'occupancy', 'hour_sin', 'hour_cos']
    if features['occupancy'] <= 0.500000:
        if features['temperature'] <= 16.950000:
            return 1
        else:
            if features['temperature'] <= 35.650000:
                if features['temperature'] <= 22.950000:
                    return 0
                else:
                    if features['brightness'] <= 549.299988:
                        if features['temperature'] <= 23.150001:
                            return 0
                        else:
                            return 0
                    else:
                        if features['brightness'] <= 571.250000:
                            return 0
                        else:
                            return 0
            else:
                if features['hour_sin'] <= 0.603553:
                    if features['hour_cos'] <= 0.915976:
                        if features['brightness'] <= 129.350006:
                            return 0
                        else:
                            return 0
                    else:
                        return 0
                else:
                    return 0
    else:
        if features['hour_cos'] <= -0.000000:
            if features['brightness'] <= 300.449997:
                if features['temperature'] <= 32.400000:
                    if features['temperature'] <= 23.849999:
                        if features['brightness'] <= 116.250000:
                            return 1
                        else:
                            return 1
                    else:
                        if features['brightness'] <= 246.900002:
                            return 1
                        else:
                            return 1
                else:
                    if features['temperature'] <= 33.400000:
                        if features['brightness'] <= 128.899998:
                            return 1
                        else:
                            return 1
                    else:
                        return 1
            else:
                if features['brightness'] <= 879.450012:
                    if features['brightness'] <= 874.600006:
                        if features['brightness'] <= 328.099991:
                            return 0
                        else:
                            return 0
                    else:
                        return 0
                else:
                    return 0
        else:
            if features['brightness'] <= 101.799999:
                if features['brightness'] <= 85.000000:
                    if features['temperature'] <= 28.050000:
                        if features['hour_cos'] <= 0.786566:
                            return 1
                        else:
                            return 1
                    else:
                        if features['hour_sin'] <= -0.129410:
                            return 1
                        else:
                            return 1
                else:
                    if features['hour_sin'] <= 0.603553:
                        return 1
                    else:
                        return 1
            else:
                if features['hour_sin'] <= 0.379410:
                    if features['temperature'] <= 19.300000:
                        return 1
                    else:
                        if features['brightness'] <= 989.699982:
                            return 1
                        else:
                            return 1
                else:
                    if features['brightness'] <= 790.049988:
                        if features['temperature'] <= 23.600000:
                            return 1
                        else:
                            return 1
                    else:
                        if features['brightness'] <= 876.149994:
                            return 1
                        else:
                            return 1


def predict_aircond(features):
    # features = dict with keys: ['temperature', 'brightness', 'occupancy', 'hour_sin', 'hour_cos']
    if features['occupancy'] <= 0.500000:
        if features['temperature'] <= 28.250000:
            if features['temperature'] <= 24.650001:
                if features['temperature'] <= 21.750000:
                    if features['hour_sin'] <= 0.982963:
                        if features['temperature'] <= 18.600000:
                            return 27.905263
                        else:
                            return 28.244565
                    else:
                        return 28.740000
                else:
                    if features['brightness'] <= 645.449982:
                        if features['temperature'] <= 22.550000:
                            return 28.375862
                        else:
                            return 28.674815
                    else:
                        if features['brightness'] <= 690.600006:
                            return 28.222222
                        else:
                            return 28.539024
            else:
                if features['temperature'] <= 26.250000:
                    if features['brightness'] <= 381.099991:
                        if features['brightness'] <= 363.350006:
                            return 28.857955
                        else:
                            return 29.500000
                    else:
                        if features['brightness'] <= 541.000000:
                            return 28.519444
                        else:
                            return 28.792500
                else:
                    if features['brightness'] <= 760.399994:
                        if features['temperature'] <= 27.750000:
                            return 28.907143
                        else:
                            return 29.076190
                    else:
                        if features['brightness'] <= 854.100006:
                            return 28.657143
                        else:
                            return 28.966667
        else:
            if features['temperature'] <= 32.549999:
                if features['temperature'] <= 29.950000:
                    if features['hour_sin'] <= -0.982963:
                        if features['temperature'] <= 29.100000:
                            return 28.600000
                        else:
                            return 28.640000
                    else:
                        if features['hour_sin'] <= -0.786566:
                            return 29.216129
                        else:
                            return 29.093156
                else:
                    if features['brightness'] <= 382.150009:
                        if features['hour_sin'] <= -0.982963:
                            return 28.980000
                        else:
                            return 29.477049
                    else:
                        if features['brightness'] <= 966.649994:
                            return 29.306140
                        else:
                            return 29.014286
            else:
                if features['temperature'] <= 36.800001:
                    if features['temperature'] <= 34.850000:
                        if features['brightness'] <= 31.049999:
                            return 29.260000
                        else:
                            return 29.609459
                    else:
                        if features['hour_cos'] <= -0.000000:
                            return 29.907143
                        else:
                            return 29.653333
                else:
                    if features['temperature'] <= 37.150000:
                        return 30.520000
                    else:
                        if features['temperature'] <= 37.750000:
                            return 29.862500
                        else:
                            return 30.176471
    else:
        if features['temperature'] <= 31.650001:
            if features['temperature'] <= 29.450000:
                if features['temperature'] <= 28.150001:
                    if features['brightness'] <= 325.400009:
                        if features['brightness'] <= 134.300003:
                            return 26.046032
                        else:
                            return 25.906757
                    else:
                        if features['brightness'] <= 393.899994:
                            return 26.121277
                        else:
                            return 26.015781
                else:
                    if features['temperature'] <= 28.849999:
                        if features['hour_cos'] <= -0.982963:
                            return 25.320000
                        else:
                            return 25.876471
                    else:
                        if features['brightness'] <= 305.049988:
                            return 25.502083
                        else:
                            return 25.802273
            else:
                if features['temperature'] <= 30.550000:
                    if features['brightness'] <= 364.800003:
                        if features['brightness'] <= 128.400002:
                            return 25.430000
                        else:
                            return 25.662000
                    else:
                        if features['brightness'] <= 724.949982:
                            return 25.309859
                        else:
                            return 25.509434
                else:
                    if features['brightness'] <= 278.699997:
                        if features['brightness'] <= 164.250000:
                            return 25.025000
                        else:
                            return 25.516667
                    else:
                        if features['temperature'] <= 31.349999:
                            return 25.117391
                        else:
                            return 24.892593
        else:
            if features['temperature'] <= 33.750000:
                if features['temperature'] <= 32.650000:
                    if features['hour_cos'] <= 0.379410:
                        if features['hour_sin'] <= 0.129410:
                            return 24.580952
                        else:
                            return 24.788235
                    else:
                        if features['brightness'] <= 458.300003:
                            return 24.740000
                        else:
                            return 25.018750
                else:
                    if features['brightness'] <= 923.250000:
                        if features['temperature'] <= 32.750000:
                            return 24.136364
                        else:
                            return 24.452000
                    else:
                        return 24.862500
            else:
                if features['temperature'] <= 35.750000:
                    if features['hour_sin'] <= -0.603553:
                        if features['temperature'] <= 34.450001:
                            return 23.981818
                        else:
                            return 23.490909
                    else:
                        if features['hour_sin'] <= 0.915976:
                            return 24.113793
                        else:
                            return 23.781818
                else:
                    if features['temperature'] <= 38.250000:
                        if features['hour_cos'] <= 0.603553:
                            return 23.496667
                        else:
                            return 23.075000
                    else:
                        if features['brightness'] <= 502.350006:
                            return 22.800000
                        else:
                            return 22.180000
