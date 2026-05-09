"""Heuristic advisory lines for MCP agents (non-authoritative vs local METAR/airport briefing)."""


def build_site_weather_advisories(snapshot: dict) -> list[str]:
    """Return concise English bullets from a SiteWeatherObservationSchema-shaped dict."""

    lines: list[str] = []

    summary = snapshot.get('conditions_summary')
    if isinstance(summary, str):
        condensed = summary.strip().lower()
        if any(k in condensed for k in ('thunderstorm', 'tornado')):
            lines.append(
                'Severe convective signal in the textual condition field — postpone dome operations and unplug sensitive gear.',
            )
        elif any(k in condensed for k in ('snow', 'sleet', 'ice')):
            lines.append('Frozen precipitation reported in conditions — icing / rig safety posture recommended.')

    clouds = snapshot.get('cloud_cover_percent')
    if isinstance(clouds, (int, float)):
        if clouds >= 90:
            lines.append(f'Heavy cloud layer ({clouds:.0f}% coverage) — expect poor transparency for deep-sky.')
        elif clouds >= 65:
            lines.append(f'Broken cloud (~{clouds:.0f}% coverage) — check local clears before exposing optics.')

    wind = snapshot.get('wind_speed_m_per_s')
    if isinstance(wind, (int, float)):
        if wind >= 14:
            lines.append(
                f'Gust-prone ambient wind (~{wind:.1f} m/s at grid point); secure cables and reconsider high-profile rigs.',
            )
        elif wind >= 10:
            lines.append(f'Elevated surface wind (~{wind:.1f} m/s) — monitor vibrations for long exposures.')

    visibility = snapshot.get('visibility_meters')
    if isinstance(visibility, (int, float)) and visibility < 3000:
        lines.append('Low horizontal visibility (<3 km snapshot) — could be humidity, fog, or smoke; visually confirm.')

    humid = snapshot.get('relative_humidity_percent')
    if isinstance(humid, (int, float)) and humid >= 90:
        lines.append('Very humid air mass — watch for dew formation on optics / electronics.')

    if not lines:
        lines.append(
            'No explicit guardrail fired from coarse OpenWeather thresholds — operators must still obey local/site rules.',
        )

    return lines
