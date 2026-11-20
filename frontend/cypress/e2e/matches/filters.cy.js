/// <reference types="cypress" />

describe('Matchs', () => {
  it('filtre les matchs par statut', () => {
    cy.intercept('GET', '**/matches*', { body: { matches: [] } }).as('matches')

    cy.visitAs('JOUEUR', '/matches')

    cy.wait('@matches')
    cy.get('[data-cy="status-filter"]').select('TERMINE')
    cy.wait('@matches').its('request.query.status').should('eq', 'TERMINE')
    cy.get('[data-cy="no-matches"]').should('be.visible')
  })

  it('affiche les informations d’un match reçu de l’API', () => {
    cy.intercept('GET', '**/matches*', {
      body: {
        matches: [
          {
            id: 12,
            status: 'A_VENIR',
            court_number: 2,
            score_team1: null,
            event: { date: '2026-11-20', time: '18:30' },
            team1: {
              company: 'Acme',
              players: [
                { first_name: 'Alex', last_name: 'Martin' },
                { first_name: 'Sam', last_name: 'Durand' },
              ],
            },
            team2: {
              company: 'Globex',
              players: [
                { first_name: 'Lou', last_name: 'Petit' },
                { first_name: 'Max', last_name: 'Bernard' },
              ],
            },
          },
        ],
      },
    }).as('matches')

    cy.visitAs('JOUEUR', '/matches')

    cy.wait('@matches')
    cy.get('[data-cy="matches-list"]').should('be.visible')
    cy.get('[data-cy="team1-company"]').should('contain', 'Acme')
    cy.get('[data-cy="team2-company"]').should('contain', 'Globex')
    cy.get('[data-cy="status-badge"]').should('contain', 'À venir')
    cy.contains('Piste 2').should('be.visible')
  })
})
