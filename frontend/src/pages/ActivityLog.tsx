import { EmptyState } from '../components/ui';
import { Hammer } from 'lucide-react';

export function ActivityLog() {
  return (
    <div className="h-full flex items-center justify-center">
      <EmptyState 
        icon={Hammer} 
        title="ActivityLog Page" 
        description="This module is scheduled for a future build phase." 
      />
    </div>
  );
}
