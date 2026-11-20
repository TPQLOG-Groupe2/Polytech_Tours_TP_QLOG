/// <reference types="cypress" />

describe('Profil', () => {
  const profile = {
    user: { email: 'test@padel.com' },
    player: {
      first_name: 'Alex',
      last_name: 'Martin',
      birth_date: '1995-04-12',
      license_number: 'L123456',
    },
  }

  it('enregistre les modifications du profil', () => {
    cy.intercept('GET', '**/profile/me', { body: profile }).as('profile')
    cy.intercept('PUT', '**/profile/me', { statusCode: 200, body: profile }).as('updateProfile')

    cy.visitAs('JOUEUR', '/profile')
    cy.wait('@profile')
    cy.get('[data-cy="first-name"]').clear().type('Camille')
    cy.get('[data-cy="save"]').click()

    cy.wait('@updateProfile').its('request.body').should('include', {
      first_name: 'Camille',
      last_name: 'Martin',
      email: 'test@padel.com',
      birth_date: '1995-04-12',
    })
    cy.get('[data-cy="success"]').should('contain', 'Profil mis à jour.')
  })

  it('affiche l’erreur renvoyée si la mise à jour échoue', () => {
    cy.intercept('GET', '**/profile/me', { body: profile }).as('profile')
    cy.intercept('PUT', '**/profile/me', {
      statusCode: 400,
      body: { detail: 'Adresse email déjà utilisée' },
    }).as('updateProfile')

    cy.visitAs('JOUEUR', '/profile')
    cy.wait('@profile')
    cy.get('[data-cy="email"]').clear().type('deja-utilise@padel.com')
    cy.get('[data-cy="save"]').click()

    cy.wait('@updateProfile')
    cy.get('[data-cy="error"]').should('contain', 'Adresse email déjà utilisée')
  })
})
