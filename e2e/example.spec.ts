import { test, expect } from '@playwright/test'

test('homepage loads', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('h1')).toContainText('agent-orchestration-machine')
})

test('counter increments', async ({ page }) => {
  await page.goto('/')
  const button = page.locator('button')
  await expect(button).toContainText('Count: 0')
  await button.click()
  await expect(button).toContainText('Count: 1')
})
