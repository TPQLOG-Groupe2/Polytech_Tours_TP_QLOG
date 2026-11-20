/// <reference types="cypress" />

describe('Résultats et classements', () => {
  it('affiche le classement et les statistiques du joueur', () => {
    cy.intercept('GET', '**/results/rankings', {
      body: {
        rankings: [
          {
            position: 1,
            company: 'Acme',
            matches_played: 4,
            wins: 3,
            losses: 1,
            sets_won: 7,
            sets_lost: 3,
            points: 9,
          },
        ],
      },
    }).as('rankings')
    cy.intercept('GET', '**/results/my-results', {
      body: {
        statistics: { total_matches: 4, wins: 3, losses: 1, win_rate: 75 },
        results: [],
      },
    }).as('myResults')

    cy.visitAs('JOUEUR', '/results')

    cy.wait(['@rankings', '@myResults'])
    cy.get('[data-cy="rankings-table"]').contains('Acme').should('be.visible')
    cy.get('[data-cy="rankings-table"]').contains('9').should('be.visible')
    cy.contains('4').should('be.visible')
    cy.contains('75%').should('be.visible')
  })

  it('indique quand aucun classement n’est disponible', () => {
    cy.intercept('GET', '**/results/rankings', { body: { rankings: [] } }).as('rankings')
    cy.intercept('GET', '**/results/my-results', {
      body: {
        statistics: { total_matches: 0, wins: 0, losses: 0, win_rate: 0 },
        results: [],
      },
    }).as('myResults')

    cy.visitAs('JOUEUR', '/results')

    cy.wait(['@rankings', '@myResults'])
    cy.get('[data-cy="rankings-table"]').should('contain', 'Aucun résultat pour le moment.')
    cy.contains("Aucun match terminé pour l'instant.").should('be.visible')
  })
})
