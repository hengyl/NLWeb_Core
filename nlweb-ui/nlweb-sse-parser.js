/**
 * NLWeb SSE Parser - Shared utility for parsing Server-Sent Event messages
 * Used by both nlweb-chat.js and nlweb-dropdown-chat.js
 */

export class NLWebSSEParser {
    /**
     * Parse an SSE message and return structured data
     * @param {Object} data - The parsed JSON data from SSE
     * @returns {Object} Parsed message with type and content
     */
    static parseMessage(data) {
        // Handle _meta message
        if (data._meta) {
            return {
                type: 'metadata',
                metadata: data._meta
            };
        }

        // Handle content array (NLWeb format)
        if (data.content && Array.isArray(data.content)) {
            const items = [];

            data.content.forEach(item => {
                // Skip text items - they're duplicates of the resource descriptions
                // Only handle resource items
                if (item.type === 'resource' && item.resource && item.resource.data) {
                    items.push({
                        type: 'resource',
                        data: item.resource.data
                    });
                }
            });

            return {
                type: 'content',
                items: items
            };
        }

        // Handle conversation_id
        if (data.type === 'conversation_id' && data.conversation_id) {
            return {
                type: 'conversation_id',
                conversation_id: data.conversation_id
            };
        }

        // Handle stream complete
        if (data.type === 'done' || data.type === 'complete') {
            return {
                type: 'complete'
            };
        }

        // Handle legacy text format
        if (data.type === 'text' || data.text) {
            return {
                type: 'text',
                text: data.content || data.text
            };
        }

        // Handle legacy item/result format
        if (data.type === 'item' || data.type === 'result' || data.title) {
            return {
                type: 'item',
                title: data.title,
                snippet: data.snippet || data.description,
                link: data.link || data.url
            };
        }

        // Unknown format
        return {
            type: 'unknown',
            data: data
        };
    }

    /**
     * Create HTML element for a resource item
     * @param {Object} resourceData - The resource data
     * @returns {HTMLElement} The created DOM element
     */
    static createResourceElement(resourceData) {
        const container = document.createElement('div');
        container.className = 'item-container';

        const content = document.createElement('div');
        content.className = 'item-content';

        // Title row with link
        const titleRow = document.createElement('div');
        titleRow.className = 'item-title-row';
        const titleLink = document.createElement('a');
        titleLink.href = resourceData.url || resourceData.grounding || '#';
        titleLink.className = 'item-title-link';
        titleLink.textContent = resourceData.name || resourceData.title || resourceData.description?.substring(0, 50) + '...' || 'Result';
        titleLink.target = '_blank';
        titleRow.appendChild(titleLink);
        content.appendChild(titleRow);

        // Site link
        if (resourceData.site) {
            const siteLink = document.createElement('a');
            siteLink.href = `/ask?site=${resourceData.site}`;
            siteLink.className = 'item-site-link';
            siteLink.textContent = resourceData.site;
            content.appendChild(siteLink);
        }

        // Description
        if (resourceData.description) {
            const description = document.createElement('div');
            description.className = 'item-description';
            description.textContent = resourceData.description;
            content.appendChild(description);
        }

        container.appendChild(content);

        // Image
        if (resourceData.image) {
            const imgWrapper = document.createElement('div');
            const img = document.createElement('img');
            img.src = resourceData.image;
            img.alt = 'Item image';
            img.className = 'item-image';
            imgWrapper.appendChild(img);
            container.appendChild(imgWrapper);
        }

        return container;
    }
}