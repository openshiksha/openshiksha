import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { Button } from '@/shared/ui';
import type { ClassroomInviteCode } from '@/types/index';

const fetchClassroomCodes = async (): Promise<ClassroomInviteCode[]> => {
  const res = await apiClient.get<ClassroomInviteCode[]>('/users/me/classroom-code/');
  return res.data;
};

const generateCode = async (classroomId: number): Promise<ClassroomInviteCode> => {
  const res = await apiClient.post<ClassroomInviteCode>('/users/me/classroom-code/', {
    classroom_id: classroomId,
  });
  return res.data;
};

interface Props {
  classroomId: number;
  classroomName: string;
}

export const ClassroomCodeWidget = ({ classroomId, classroomName }: Props) => {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);

  const { data: codes } = useQuery<ClassroomInviteCode[]>({
    queryKey: ['classroom-codes'],
    queryFn: fetchClassroomCodes,
  });

  const generateMutation = useMutation({
    mutationFn: () => generateCode(classroomId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['classroom-codes'] }),
  });

  const myCode = codes?.find((c) => c.classroom_id === classroomId);

  const handleCopy = () => {
    if (!myCode) return;
    navigator.clipboard.writeText(myCode.code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
        Classroom Join Code
      </p>
      {myCode ? (
        <div className="flex flex-wrap items-center gap-2">
          <code className="rounded-lg bg-brand-50 px-3 py-1.5 font-mono text-sm font-bold tracking-widest text-brand-800 ring-1 ring-brand-100">
            {myCode.code}
          </code>
          <Button variant="ghost" size="sm" onClick={handleCopy}>
            {copied ? 'Copied!' : 'Copy'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            title={`Regenerate join code for ${classroomName}`}
          >
            {generateMutation.isPending ? '…' : 'Regenerate'}
          </Button>
        </div>
      ) : (
        <Button
          variant="brand"
          size="sm"
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
        >
          {generateMutation.isPending ? 'Generating…' : 'Generate Join Code'}
        </Button>
      )}
    </div>
  );
};
