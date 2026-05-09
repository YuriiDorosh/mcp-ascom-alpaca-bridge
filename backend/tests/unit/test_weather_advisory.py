from application.api.telescope.weather_advisory import build_site_weather_advisories


def test_weather_advisory_flags_dense_cloud_cover():
    lines = build_site_weather_advisories(
        {
            'conditions_summary': 'few clouds',
            'cloud_cover_percent': 93,
            'wind_speed_m_per_s': 2,
            'relative_humidity_percent': 50,
            'visibility_meters': 10000,
        },
    )
    assert any('cloud' in ln.lower() for ln in lines)


def test_weather_advisory_fallback_line_when_signals_mild():
    lines = build_site_weather_advisories(
        {
            'conditions_summary': 'clear sky',
            'cloud_cover_percent': 15,
            'wind_speed_m_per_s': 2,
            'visibility_meters': 10000,
            'relative_humidity_percent': 40,
        },
    )
    assert any('No explicit guardrail' in ln for ln in lines)
