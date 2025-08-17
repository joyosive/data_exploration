WITH revenue_calculation AS (
  SELECT
    block_date,
    block_time,
    tx_hash,
    feature,
    trader,
    is_stablecoin_pair,
    usd_value,

    -- Calculate revenue based on feature type and swap size
    CASE
      -- SafeApps revenue calculation (percentage of swap volume)
      WHEN feature = 'cow safeapp' THEN usd_value * 0.00045  -- 0.045%
      WHEN feature = 'oneinch safeapp' THEN usd_value * 0.00053  -- 0.053%
      WHEN feature = 'kyberswap' THEN usd_value * 0.00045  -- 0.045%

      -- Native Swaps revenue calculation (tiered structure)
      WHEN feature IN ('native swaps', 'native swaps lifi') THEN
        CASE
          -- Stablecoin pairs
          WHEN is_stablecoin_pair = 1 THEN
            CASE
              WHEN usd_value <= 100000 THEN usd_value * 0.001     -- 0.10%
              WHEN usd_value <= 1000000 THEN usd_value * 0.0007   -- 0.07%
              ELSE usd_value * 0.0005                             -- 0.05%
            END
          -- Non-stablecoin pairs
          ELSE
            CASE
              WHEN usd_value <= 100000 THEN usd_value * 0.0035    -- 0.35%
              WHEN usd_value <= 1000000 THEN usd_value * 0.002    -- 0.20%
              ELSE usd_value * 0.001                              -- 0.10%
            END
        END

      -- Default case for unknown features
      ELSE 0
    END AS revenue_usd

  FROM dune.safe.result_testset
)

SELECT
  ROUND(SUM(revenue_usd), 2) AS total_revenue_usd,
  COUNT(*) AS total_transactions,
  ROUND(SUM(usd_value), 2) AS total_volume_usd,
  ROUND(AVG(revenue_usd), 4) AS avg_revenue_per_transaction,
  ROUND(SUM(revenue_usd) / SUM(usd_value) * 100, 4) AS overall_revenue_rate_percent,

  -- Breakdown by feature
  ROUND(SUM(CASE WHEN feature = 'cow safeapp' THEN revenue_usd ELSE 0 END), 2) AS cow_safeapp_revenue,
  ROUND(SUM(CASE WHEN feature = 'oneinch safeapp' THEN revenue_usd ELSE 0 END), 2) AS oneinch_safeapp_revenue,
  ROUND(SUM(CASE WHEN feature = 'kyberswap' THEN revenue_usd ELSE 0 END), 2) AS kyberswap_revenue,
  ROUND(SUM(CASE WHEN feature IN ('native swaps', 'native swaps lifi') THEN revenue_usd ELSE 0 END), 2) AS native_swaps_revenue,

  -- Breakdown by pair type for native swaps
  ROUND(SUM(CASE WHEN feature IN ('native swaps', 'native swaps lifi') AND is_stablecoin_pair = 1 THEN revenue_usd ELSE 0 END), 2) AS native_stablecoin_revenue,
  ROUND(SUM(CASE WHEN feature IN ('native swaps', 'native swaps lifi') AND is_stablecoin_pair = 0 THEN revenue_usd ELSE 0 END), 2) AS native_non_stablecoin_revenue

FROM revenue_calculation