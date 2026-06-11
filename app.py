# Qator 1770-1796 to'g'rilangan versiya

def predict_collapse(
    model,
    rf: RandomForestClassifier,
    scaler: StandardScaler,
    X_raw: np.ndarray,
) -> np.ndarray:
    """
    [FIX #29] assert → ValueError
    """
    if X_raw.shape[1] != 7:
        raise ValueError(f"Expected 7 features, got {X_raw.shape[1]}")
    X_sc = scaler.transform(X_raw)
    if model is not None:
        model.eval()
        with torch.no_grad():
            nn_pred = model(
                torch.tensor(X_sc, dtype=torch.float32).to(device)
            ).cpu().numpy()
    else:
        nn_pred = np.zeros((X_raw.shape[0], 1))

    proba = rf.predict_proba(X_sc)
    rf_pred = proba[:, 1].reshape(-1, 1) if proba.shape[1] >= 2 else proba[:, 0].reshape(-1, 1)
    # [FIX C-16] When model=None (no PyTorch), use RF only
    w_nn = 0.6 if (nn_pred is not None and np.any(nn_pred != 0.0)) else 0.0
    w_rf = 1.0 - w_nn
    return w_nn * nn_pred + w_rf * rf_pred
