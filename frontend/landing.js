// Injeta a marca do logo (calendário + check) em todos os pontos de uso.
const logoTemplate = document.getElementById('tpl-logo')
document.querySelectorAll('.logo-mark').forEach((el) => {
  el.appendChild(logoTemplate.content.cloneNode(true))
})

// Header ganha sombra ao rolar a página.
const header = document.getElementById('header')
const onScroll = () => {
  header.classList.toggle('is-scrolled', window.scrollY > 8)
}
onScroll()
window.addEventListener('scroll', onScroll, { passive: true })

// Menu mobile.
const navToggle = document.getElementById('navToggle')
const nav = document.getElementById('nav')

function closeNav() {
  document.body.classList.remove('nav-open')
  navToggle.setAttribute('aria-expanded', 'false')
}

navToggle.addEventListener('click', () => {
  const isOpen = document.body.classList.toggle('nav-open')
  navToggle.setAttribute('aria-expanded', String(isOpen))
})

nav.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', closeNav)
})

window.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeNav()
})

// Revela seções ao entrar na tela.
const revealTargets = document.querySelectorAll('.reveal')

if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          observer.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.15 }
  )
  revealTargets.forEach((el) => observer.observe(el))
} else {
  revealTargets.forEach((el) => el.classList.add('is-visible'))
}
