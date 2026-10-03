
SELECT COUNT(single_bid)               AS labelled,
       ROUND(AVG(single_bid) * 100, 1) AS single_bid_pct
FROM tenders
;

SELECT dept_main,
       COUNT(single_bid)               AS labelled,
       ROUND(AVG(single_bid) * 100, 1) AS single_bid_pct
FROM tenders
WHERE single_bid IS NOT NULL
GROUP BY dept_main
HAVING COUNT(single_bid) >= 50
ORDER BY single_bid_pct DESC
;

SELECT strftime('%Y', published_date)  AS year,
       COUNT(single_bid)               AS labelled,
       ROUND(AVG(single_bid) * 100, 1) AS single_bid_pct
FROM tenders
WHERE single_bid IS NOT NULL
GROUP BY year
ORDER BY year
;

SELECT CASE
         WHEN days_since_same IS NULL THEN '1 First-time'
         WHEN days_since_same = 0     THEN '2 Same-day lot'
         WHEN days_since_same <= 60   THEN '3 Re-posted 1-60 days'
         WHEN days_since_same <= 300  THEN '4 Re-posted 2-10 months'
         ELSE                              '5 Re-posted after 10 months'
       END                              AS repeat_type,
       COUNT(single_bid)               AS labelled,
       ROUND(AVG(single_bid) * 100, 1) AS single_bid_pct
FROM tenders
WHERE single_bid IS NOT NULL
GROUP BY repeat_type
ORDER BY repeat_type
;
