
tautologies_p = [('1. Prawo niesprzeczności', '(~(p AND ~p))'),
                 ('2. Prawo identyczności', 'p => p'),
                 ('3. Prawo podwójnego zaprzeczenia', '~(~p) => p'),
                 ('4. Prawo wyłączonego środka', '(p OR (~p))'),
                 ('5. Prawo niesprzeczności', '(~(p AND (~p)))'),
                 ('6. Prawo idempotentności alternatywy', '(p OR p) <=> p'),
                 ('7. Prawo idempotentności koniunkcji', '(p AND p) <=> p'),
                 ('8. Pierwsze prawo Claviusa', '(p => (~p)) => (~p)'),
                 ('9. Drugie prawo Claviusa', '((~p) => p) => p')]

tautologies_pq = [('10. Prawo Dunsa Szkota', '(~q) => (q => p)'),
                  ('11. Pierwsze prawo symplifikacji', 'q => (p => q)'),
                  ('12. . Drugie prawo symplifikacji', '(q AND p) => q'),
                  ('13. Trzecie prawo symplifikacji', 'q => (q OR p)'),
                  ('14. Pierwsze prawo de Morgana', '(~(q AND p)) <=> ((~q) OR (~p))'),
                  ('15. Drugie prawo de Morgana', '(~(q OR p)) <=> ((~q) AND (~p))'),
                  ('16. Pierwsze prawo definiowania implikacji', '(q => p) <=> (p OR (~q))'),
                  ('17. Pierwsze prawo definiowania alternatywy wykluczającej', '(q XOR p) <=> ((q AND (~p)) OR ((~q) AND p))'),
                  ('18. Drugie prawo definiowania alternatywy wykluczającej', '(q XOR p) <=> ((q OR p) AND (~(q AND p)))'),
                  ('19. Prawo kontrapozycji', '(q => p) <=> ((~p) => (~q))'),
                  ('20. Prawo transpozycji', '(q => (~p)) <=> (p => (~q))'),
                  ('21. Prawo prawo redukcji do absurdu', '(q => (p AND (~p))) => (~q)'),
                  ('22. Drugie prawo redukcji do absurdu', '((q => p) AND (q => (~p))) => (~q)'),
                  ('23. Prawo równoważności przeciwnych implikacji', '(q <=> p) <=> ((q => p) AND (p => q))')]

tautologies_pqr = [('24. Prawo przechodniości implikacji', '((r => q) AND (q => p)) => (r => p)'),
                   ('25. Prawo komutacji', '(r => (q => p)) => (q => (r => p))'),
                   ('26. Prawo importacji', '(r => (q => p)) => ((r AND q) => p)'),
                   ('27. Prawo exportacji', '((r AND q) => p) => (r => (q => p))'),
                   ('28. Prawo rozdzielania poprzednika', '(( r OR q) => p) => ((r => p) AND (q => p))'),
                   ('29. Pierwsze prawo ekstensjonalności', '(r <=> q) => ((r AND p) <=> (q AND p))')]

tautologies_pqrs = [('30. Prawo łączenia alternatywnego stronami', '((s => r) AND (q => p)) => ((s OR q) => (r OR p))'),
                    ('31. Prawo łączenia koniunkcyjnego stronami', '((s => r) AND (q => p)) => ((s AND q) => (r AND p))')]

all_tautologies = []
for item in tautologies_p:
    all_tautologies.append(item)
for item in tautologies_pq:
    all_tautologies.append(item)
for item in tautologies_pqr:
    all_tautologies.append(item)
for item in tautologies_pqrs:
    all_tautologies.append(item)

#all_tautologies=[('21. Prawo prawo redukcji do absurdu', '(q => (p AND (~p))) => (~q)')]