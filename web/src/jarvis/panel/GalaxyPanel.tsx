/**
 * GalaxyPanel.tsx — Phase J3: Galaxy (agent knowledge graph) as Panel #1.
 *
 * Wraps GalaxyView (untouched) inside the PanelLayer slide-in drawer.
 * GalaxyView is only mounted while the panel is open — this prevents its
 * ResizeObserver + polling loop from running constantly in the background.
 */

import { PanelLayer } from './PanelLayer';
import { usePanelStore } from './panelStore';
import GalaxyView from '../../components/GalaxyView';

export function GalaxyPanel() {
  const { openPanel } = usePanelStore();
  const isOpen = openPanel === 'galaxy';

  return (
    <PanelLayer id="galaxy" title="Agent Knowledge Graph" width={540}>
      <div style={{ height: '100%', minHeight: 0 }}>
        {/* Only mount GalaxyView when panel is open — prevents background render loop */}
        {isOpen && <GalaxyView />}
      </div>
    </PanelLayer>
  );
}
