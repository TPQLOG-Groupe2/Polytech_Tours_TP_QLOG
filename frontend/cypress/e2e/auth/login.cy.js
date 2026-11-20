/// <reference types="cypress" />

describe('Authentification', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
  })

  it("affiche l'accueil et propose de se connecter", () => {
    cy.visit('/')

    cy.contains('h1', 'Corpo Padel').should('be.visible')
    cy.get('[data-cy="home-login"]').should('be.visible')
    cy.get('[data-cy="nav-login"]').should('be.visible')
  })

  it('redirige un visiteur vers la connexion pour une page protégée', () => {
    cy.visit('/planning')

    cy.location('pathname').should('eq', '/login')
    cy.location('search').should('contain', 'redirect=%2Fplanning')
    cy.get('[data-cy="email"]').should('be.visible')
    cy.get('[data-cy="password"]').should('be.visible')
  })

  it('affiche une erreur lorsque les identifiants sont refusés', () => {
    cy.intercept('POST', '**/auth/login', {
      statusCode: 401,
      body: { detail: 'Identifiants incorrects' },
    }).as('login')

    cy.visit('/login')
    cy.get('[data-cy="email"]').type('joueur@padel.com')
    cy.get('[data-cy="password"]').type('mauvais-mot-de-passe')
    cy.get('[data-cy="submit"]').click()

    cy.wait('@login')
    cy.get('[data-cy="login-error"]')
      .should('be.visible')
      .and('contain', 'Identifiants incorrects')
    cy.window().should((window) => {
      expect(window.localStorage.getItem('token')).to.be.null
    })
  })

  it('connecte un joueur, le redirige vers sa page puis le déconnecte', () => {
    cy.intercept('POST', '**/auth/login', {
      statusCode: 200,
      body: {
        access_token: 'test-token',
        user: {
          id: 1,
          email: 'joueur@padel.com',
          role: 'JOUEUR',
          must_change_password: false,
        },
      },
    }).as('login')
    cy.intercept('GET', '**/profile/me', {
      statusCode: 200,
      body: { player: { first_name: 'Camille' } },
    }).as('profile')
    cy.intercept('GET', '**/events*', {
      statusCode: 200,
      body: { events: [] },
    }).as('events')

    cy.visit('/planning')
    cy.get('[data-cy="email"]').type('joueur@padel.com')
    cy.get('[data-cy="password"]').type('mot-de-passe')
    cy.get('[data-cy="submit"]').click()

    cy.wait('@login')
    cy.wait('@profile')
    cy.wait('@events')
    cy.location('pathname').should('eq', '/planning')
    cy.contains('h1', 'Planning').should('be.visible')
    cy.get('[data-cy="logout"]').should('be.visible')
    cy.window().should((window) => {
      expect(window.localStorage.getItem('token')).to.eq('test-token')
    })

    cy.get('[data-cy="logout"]').click()
    cy.location('pathname').should('eq', '/login')
    cy.window().should((window) => {
      expect(window.localStorage.getItem('token')).to.be.null
      expect(window.localStorage.getItem('user')).to.be.null
    })
  })
})
