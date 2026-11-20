/// <reference types="cypress" />

// Prépare une session front pour tester une page sans rejouer le formulaire de login.
Cypress.Commands.add('visitAs', (role, path) => {
  cy.visit(path, {
    onBeforeLoad(window) {
      window.localStorage.setItem('token', 'test-token')
      window.localStorage.setItem(
        'user',
        JSON.stringify({ id: 1, email: 'test@padel.com', role }),
      )
    },
  })
})
