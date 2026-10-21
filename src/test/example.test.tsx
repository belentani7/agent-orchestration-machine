import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText('Count: 0')).toBeInTheDocument()
  })

  it('increments count on button click', async () => {
    render(<App />)
    const button = screen.getByRole('button')
    await import('@testing-library/user-event').then(u => u.default.click(button))
    expect(screen.getByText('Count: 1')).toBeInTheDocument()
  })
})
