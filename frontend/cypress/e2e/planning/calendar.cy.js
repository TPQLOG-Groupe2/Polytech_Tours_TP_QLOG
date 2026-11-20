/// <reference types="cypress" />

describe('Planning', () => {
  it('permet de naviguer entre les mois du calendrier', () => {
    cy.intercept('GET', '**/events*', { body: { events: [] } }).as('events')

    cy.visitAs('JOUEUR', '/planning')
    cy.wait('@events')

    cy.get('[data-cy="month-label"]').invoke('text').then((initialMonth) => {
      cy.contains('button', 'Mois suivant').click()
      cy.wait('@events')
      cy.get('[data-cy="month-label"]').should(($month) => {
        expect($month.text()).not.to.eq(initialMonth)
      })

      cy.contains('button', 'Mois précédent').click()
      cy.wait('@events')
      cy.get('[data-cy="month-label"]').should('have.text', initialMonth)
    })
  })

  it('affiche les matchs d’un événement sélectionné dans le calendrier', () => {
    const today = new Date()
    const eventDate = [
      today.getFullYear(),
      String(today.getMonth() + 1).padStart(2, '0'),
      String(today.getDate()).padStart(2, '0'),
    ].join('-')

    cy.intercept('GET', '**/events*', {
      body: {
        events: [
          {
            id: 3,
            event_date: eventDate,
            event_time: '18:30',
            matches: [
              {
                id: 12,
                court_number: 2,
                team1: { company: 'Acme' },
                team2: { company: 'Globex' },
              },
            ],
          },
        ],
      },
    }).as('events')

    cy.visitAs('JOUEUR', '/planning')
    cy.wait('@events')

    cy.get('button.aspect-square')
      .filter((_, button) => button.textContent.trim() === String(today.getDate()))
      .click()
    cy.contains(`Événements du ${eventDate}`).should('be.visible')
    cy.contains('Piste 2').should('be.visible')
    cy.contains('Acme vs Globex').should('be.visible')
  })
})
