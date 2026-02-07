import {expect} from '@playwright/test';

export class MapPage {
    /**
     * @param {import('@playwright/test').Page} page
     */
    constructor(page) {
        this.page = page;
        this.header = page.locator('h1', {hasText: 'MARITIME VTS'});
        this.mapContainer = page.locator('.leaflet-container');
        this.placeholder = page.getByText('Monitoring Norwegian EEZ...');

        // Status and Alerts
        this.statusConnected = page.locator('.text-green-500');
        this.alertItems = page.locator('div[class*="bg-red-950/40"]');

        // Vessels and Popups
        this.vesselIcon = page.locator('.custom-vessel-icon');
        this.popup = page.locator('.leaflet-popup-content');
    }

    async goto() {
        await this.page.goto('/');
    }

    async expectMapLoaded() {
        await expect(this.header).toBeVisible();
        await expect(this.mapContainer).toBeVisible();
        await expect(this.placeholder).toBeVisible();
    }

    async expectLiveConnection() {
        await expect(this.statusConnected).toBeVisible({timeout: 10000});
    }

    async clickFirstVessel() {
        const icon = this.vesselIcon.first();
        await expect(icon).toBeVisible({timeout: 15000});
        await icon.evaluate(node => node.click());
    }

    async expectVesselPopupDetails() {
        await expect(this.popup).toBeVisible();
        await expect(this.popup).toContainText('MMSI');
        await expect(this.popup).toContainText('SOG (Speed)');
    }
}