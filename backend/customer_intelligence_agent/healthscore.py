from tables import *
from datetime import date
from sqlalchemy import text

Session = sessionmaker(bind=engine)
session = Session()

def health_score(account_id:str, as_of_date:date):
    usage_score_result = session.execute(text("""WITH usage_metrics AS (
            SELECT
                :account_id AS account_id,

                (
                    CAST(:as_of_date AS DATE) -
                    MIN(timestamp)::date
                ) AS account_age_days,

                COUNT(event_id) FILTER (
                    WHERE timestamp::date
                    BETWEEN CAST(:as_of_date AS DATE) - 4
                        AND CAST(:as_of_date AS DATE)
                ) AS current_5d_events,

                COUNT(event_id) FILTER (
                    WHERE timestamp::date
                    BETWEEN CAST(:as_of_date AS DATE) - 9
                        AND CAST(:as_of_date AS DATE) - 5
                ) AS previous_5d_events,

                COUNT(event_id) FILTER (
                    WHERE timestamp::date
                    BETWEEN CAST(:as_of_date AS DATE) - 14
                        AND CAST(:as_of_date AS DATE) - 10
                ) AS older_5d_events

            FROM usage_events
            WHERE account_id = :account_id
        )

        SELECT
            account_id,
            current_5d_events,
            previous_5d_events,
            older_5d_events,

            CASE

                WHEN current_5d_events = 0
                    AND previous_5d_events = 0
                THEN 'INACTIVE'

                WHEN current_5d_events = 0
                    AND previous_5d_events > 0
                THEN 'INACTIVE'

                WHEN previous_5d_events = 0
                    AND current_5d_events > 0
                    AND account_age_days >= 15
                    AND older_5d_events > 0
                THEN 'RECOVERING'

                WHEN previous_5d_events = 0
                    AND current_5d_events > 0
                    AND account_age_days >= 15
                    AND older_5d_events = 0
                THEN 'NEW_ACTIVITY'

                WHEN previous_5d_events = 0
                    AND current_5d_events > 0
                THEN 'NO_BASELINE'

                WHEN ((current_5d_events - previous_5d_events)::numeric
                    / previous_5d_events) >= 0.20
                THEN 'EXCELLENT'

                WHEN ((current_5d_events - previous_5d_events)::numeric
                    / previous_5d_events) >= 0
                THEN 'HEALTHY'

                WHEN ((current_5d_events - previous_5d_events)::numeric
                    / previous_5d_events) >= -0.20
                THEN 'WARNING'

                ELSE 'RISK'

            END AS usage_status,

            CASE

                WHEN current_5d_events = 0
                    AND previous_5d_events = 0
                THEN 0

                WHEN current_5d_events = 0
                    AND previous_5d_events > 0
                THEN 0

                WHEN previous_5d_events = 0
                    AND current_5d_events > 0
                    AND account_age_days >= 15
                    AND older_5d_events > 0
                THEN 30

                WHEN previous_5d_events = 0
                    AND current_5d_events > 0
                    AND account_age_days >= 15
                    AND older_5d_events = 0
                THEN 60

                WHEN previous_5d_events = 0
                    AND current_5d_events > 0
                THEN 30

                WHEN ((current_5d_events - previous_5d_events)::numeric
                    / previous_5d_events) >= 0.20
                THEN 60

                WHEN ((current_5d_events - previous_5d_events)::numeric
                    / previous_5d_events) >= 0
                THEN 45

                WHEN ((current_5d_events - previous_5d_events)::numeric
                    / previous_5d_events) >= -0.20
                THEN 25

                ELSE 10

            END AS usage_score

        FROM usage_metrics;"""),
        {
            "account_id": account_id,
            "as_of_date": as_of_date
        }).one()

    ticket_score_result = session.execute(text("""
        WITH ticket_window AS (
            SELECT *
            FROM tickets
            WHERE account_id = :account_id
            AND created_at >= (CAST(:as_of_date AS DATE) - INTERVAL '30 days')
            AND created_at < (CAST(:as_of_date AS DATE) + INTERVAL '1 day')
        ),

        ticket_metrics AS (
            SELECT
                COUNT(*) AS ticket_volume,

                COUNT(*) FILTER (
                    WHERE LOWER(priority) = 'critical'
                )::FLOAT AS critical_count,

                COUNT(*) FILTER (
                    WHERE LOWER(priority) = 'high'
                )::FLOAT AS high_count,

                COUNT(*) FILTER (
                    WHERE LOWER(status) IN ('resolved', 'closed')
                ) AS resolved_closed_count,

                AVG(
                    CASE
                        WHEN LOWER(status) IN ('resolved', 'closed')
                            AND resolved_at IS NOT NULL
                        THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) / 86400.0
                    END
                ) AS avg_resolution_days

            FROM ticket_window
        ),

        scored AS (
            SELECT
                ticket_volume,

                ROUND(
                    (
                        CASE
                            WHEN ticket_volume = 0 THEN 0
                            ELSE ((critical_count + high_count) * 100.0 / ticket_volume)
                        END
                    )::numeric,
                    2
                ) AS critical_high_pct,

                ROUND(
                    COALESCE(avg_resolution_days, 0)::numeric,
                    2
                ) AS avg_resolution_days,

                /* ----------------------------
                Volume Score (0-20)
                ---------------------------- */
                CASE
                    WHEN ticket_volume <= 1 THEN 20
                    WHEN ticket_volume = 2 THEN 15
                    WHEN ticket_volume = 3 THEN 10
                    WHEN ticket_volume = 4 THEN 5
                    ELSE 0
                END AS volume_score,

                /* ----------------------------
                Severity Score (0-10)
                ---------------------------- */
                CASE
                    WHEN ticket_volume = 0 THEN 10

                    WHEN ((critical_count + high_count) * 100.0 / ticket_volume) < 30
                        THEN 10

                    WHEN ((critical_count + high_count) * 100.0 / ticket_volume) < 50
                        THEN 7

                    WHEN ((critical_count + high_count) * 100.0 / ticket_volume) < 70
                        THEN 3

                    ELSE 0
                END AS severity_score,

                /* ----------------------------
                Resolution Score (0-10)
                ---------------------------- */
                CASE
                    WHEN avg_resolution_days IS NULL THEN 10

                    WHEN avg_resolution_days < 5 THEN 10
                    WHEN avg_resolution_days < 9 THEN 7
                    WHEN avg_resolution_days < 14 THEN 4
                    ELSE 0
                END AS resolution_score

            FROM ticket_metrics
        )

        SELECT
            ticket_volume,
            critical_high_pct,
            avg_resolution_days,

            volume_score,
            severity_score,
            resolution_score,

            (
                volume_score +
                severity_score +
                resolution_score
            ) AS ticket_score

        FROM scored;"""),{"account_id":account_id,"as_of_date":as_of_date}).fetchone()
    result = dict(usage_score_result._mapping) | dict(ticket_score_result._mapping)
    result["total_score"] = usage_score_result.usage_score + ticket_score_result.ticket_score
    return result

def all_health_score(as_of_date : date):
        all_accounts = session.query(Account.account_id).all()
        all_result = []
        for account_id in all_accounts:
            result = health_score(account_id=account_id[0],as_of_date=as_of_date)
            all_result.append(result)
        return all_result










