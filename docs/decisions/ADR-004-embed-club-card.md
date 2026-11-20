# ADR-004 — Embed-карта + карточка клуба (лид, SpotScore pending)

**Статус:** принято (2026-11-19)  
**Контекст:** SpotMap должен встраиваться на mywavewake.ru и будущий сайт Московского отделения ФВЛС; нужна полезная карточка клуба без нарушения канона рейтинга и MVP без booking marketplace.

## Решение

1. **Канал встраивания:** публичная страница `/embed` (iframe), темы `?host=mywave|fvls`.
2. **Записаться:** только lead-CTA на внешние контакты клуба (booking_url → WhatsApp → Telegram → телефон → сайт). Слоты/оплата SpotMap — вне скоупа.
3. **Рейтинг в UI:** всегда `spot_score.status = pending`, подпись «Появится позже», пока нет валидного SpotScore по формуле v1. Числовой балл не выдумывать.
4. **Сбор данных:** клиентский чеклист из 10 пунктов удобства ([Client_Convenience_Checklist_v1.md](../03_scoring/Client_Convenience_Checklist_v1.md)) мапится в домены SpotScore; факты хранятся как known/unknown, missing ≠ false/no.
5. **Публичный API:** `GET /v1/public/places/{id}` для published spot / cable_installation (passport-lite + contacts + convenience + pending score).
6. **Frame/CORS:** allowlist хостов (localhost, mywavewake.ru, позже ФВЛС); модераторская очередь на `/embed` не показывается.

## Последствия

- Карточка полезна до появления SpotScore.
- Реклама/продвижение не участвует в score (канон п.6–8 DECISIONS).
- Claim Spot / Business Free — следующий этап.
