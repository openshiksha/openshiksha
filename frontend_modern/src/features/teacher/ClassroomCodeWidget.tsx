import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
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
    <div className="mt-3 pt-3 border-t border-gray-100">
      <p className="text-xs font-medium text-gray-500 mb-2">Classroom Join Code</p>
      {myCode ? (
        <div className="flex items-center gap-2">
          <code className="px-3 py-1.5 bg-indigo-50 text-indigo-700 font-mono text-sm font-bold rounded-lg tracking-widest">
            {myCode.code}
          </code>
          <button
            onClick={handleCopy}
            className="text-xs px-2.5 py-1.5 rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="text-xs px-2.5 py-1.5 rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
            title={`Regenerate join code for ${classroomName}`}
          >
            {generateMutation.isPending ? '…' : 'Regenerate'}
          </button>
        </div>
      ) : (
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="text-xs px-3 py-1.5 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 transition-colors disabled:opacity-50"
        >
          {generateMutation.isPending ? 'Generating…' : 'Generate Join Code'}
        </button>
      )}
    </div>
  );
};
