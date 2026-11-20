/// <reference types="cypress" />

describe('Administration', () => {
  it('empêche un joueur d’accéder à l’administration', () => {
    cy.visitAs('JOUEUR', '/admin')

    cy.location('pathname').should('eq', '/')
    cy.contains('h1', 'Corpo Padel').should('be.visible')
    cy.get('[data-cy="nav-admin"]').should('not.exist')
  })

  it('affiche les onglets et formulaires d’administration', () => {
    cy.intercept('GET', '**/players', { body: { players: [] } }).as('players')
    cy.intercept('GET', '**/teams', { body: { teams: [] } }).as('teams')
    cy.intercept('GET', '**/pools', { body: { pools: [] } }).as('pools')

    cy.visitAs('ADMINISTRATEUR', '/admin')

    cy.wait(['@players', '@teams', '@pools'])
    cy.contains('h1', 'Administration').should('be.visible')
    cy.get('[data-cy="nav-admin"]').should('be.visible')
    cy.get('[data-cy="players-table"]').should('be.visible')
    cy.get('[data-cy="tab-teams"]').click()
    cy.get('[data-cy="t-submit"]').should('be.visible')
    cy.get('[data-cy="tab-accounts"]').click()
    cy.contains('Créer un compte joueur').should('be.visible')
  })

  it('crée un compte pour un joueur sans compte', () => {
    cy.intercept('GET', '**/players', {
      body: {
        players: [
          {
            id: 7,
            first_name: 'Alex',
            last_name: 'Martin',
            company: 'Acme',
            license_number: 'L123456',
            has_account: false,
          },
        ],
      },
    }).as('players')
    cy.intercept('GET', '**/teams', { body: { teams: [] } }).as('teams')
    cy.intercept('GET', '**/pools', { body: { pools: [] } }).as('pools')
    cy.intercept('POST', '**/admin/accounts/create', {
      statusCode: 201,
      body: { temporary_password: 'Temp@123456789', email: 'alex@padel.com' },
    }).as('createAccount')

    cy.visitAs('ADMINISTRATEUR', '/admin')
    cy.wait(['@players', '@teams', '@pools'])
    cy.get('[data-cy="tab-accounts"]').click()
    cy.get('[data-cy="acc-submit"]').should('be.disabled')
    cy.get('[data-cy="acc-player"]').select('7')
    cy.get('[data-cy="acc-submit"]').click()

    cy.wait('@createAccount').its('request.body').should('deep.equal', {
      player_id: 7,
      role: 'JOUEUR',
    })
    cy.get('[data-cy="temp-password"]')
      .should('contain', 'alex@padel.com')
      .and('contain', 'Temp@123456789')
  })
})
