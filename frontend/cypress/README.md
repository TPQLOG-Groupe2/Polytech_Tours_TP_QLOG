# Tests Cypress

Les specs sont rangées par fonctionnalité dans `e2e/`. Chaque fichier `.cy.js`
couvre un parcours ciblé :

```text
cypress/
├── e2e/
│   ├── admin/       # rôles et actions d’administration
│   ├── auth/        # connexion, déconnexion et accès protégé
│   ├── matches/     # liste et filtres des matchs
│   ├── planning/    # calendrier et événements
│   ├── profile/     # consultation et modification du profil
│   └── results/     # résultats et classements
└── support/
    ├── commands.js  # commandes Cypress communes (cy.visitAs)
    └── e2e.js       # chargement du support
```

Les réponses API sont simulées avec `cy.intercept()` afin que ces tests
éprouvent le parcours front de façon reproductible. `cy.visitAs(role, path)`
prépare une session locale pour les tests qui ne portent pas sur le formulaire
de connexion.

Depuis `frontend/` :

```bash
npm run cypress:run   # toutes les specs en mode headless
npm run cypress:open  # interface interactive
```
