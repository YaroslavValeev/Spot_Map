# SpotScore — standalone reference

Референсная формула из предыдущего пакета, только Python stdlib. Это **не** backend приложения и не подтверждённый публичный рейтинг.

```bash
python -m unittest discover -s reference/scoring -p "test_*.py" -v
python reference/scoring/spotmap_score_v1.py
```

При интеграции перенести код в настоящее Python-package и обновить тесты, сохраняя исходный reference и версию формулы.
