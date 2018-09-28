import reframe as rfm
import reframe.utility.sanity as sn


@rfm.parameterized_test([True], [False])
class OpenaccCudaCpp(rfm.RegressionTest):
    def __init__(self, withmpi):
        super().__init__()
        name_suffix = 'WithMPI' if withmpi else 'WithoutMPI'
        self.name = 'OpenaccCudaCPP' + name_suffix
        self.descr = 'test for OpenACC, CUDA, MPI, and C++'
        self.valid_systems = ['daint:gpu', 'dom:gpu', 'kesch:cn']
        self.valid_prog_environs = ['PrgEnv-cray', 'PrgEnv-pgi']
        self.build_system = 'Make'
        if self.current_system.name in ['daint', 'dom']:
            self.modules = ['craype-accel-nvidia60']
            self._pgi_flags = '-O2 -acc -ta=tesla:cc60 -Mnorpath -lstdc++'
            self._env_variables = {
                'MPICH_RDMA_ENABLED_CUDA': '1',
                'CRAY_CUDA_MPS': '1'
            }
            self.num_tasks = 12
            self.num_tasks_per_node = 12
            self.num_gpus_per_node = 1
            self._nvidia_sm = '60'
        elif self.current_system.name in ['kesch']:
            self.modules = ['craype-accel-nvidia35']
            self._pgi_flags = '-O2 -acc -ta=tesla,cc35,cuda8.0'
            self._env_variables = {
                'MPICH_RDMA_ENABLED_CUDA': '1',
                'MV2_USE_CUDA': '1',
                'G2G': '1'
            }
            self.num_tasks = 8
            self.num_tasks_per_node = 8
            self.num_gpus_per_node = 8
            self._nvidia_sm = '37'

        if withmpi:
            self.mpiflag = '-DUSE_MPI'
        else:
            self.mpiflag = ''
            self.num_tasks = 1
            self.num_tasks_per_node = 1
            self.num_gpus_per_node = 1

        self.executable = 'openacc_cuda_mpi_cppstd'
        self.sanity_patterns = sn.assert_found(r'Result:\s+OK', self.stdout)
        self.maintainers = ['AJ', 'VK']
        self.tags = {'production'}

    def setup(self, partition, environ, **job_opts):
        # Set nvcc flags
        self.build_system.cxxflags = (
            ['-lcublas -lcudart -arch=sm_%s' % self._nvidia_sm]
        )
        if environ.name.startswith('PrgEnv-cray'):
            self.build_system.fflags = ['-O2 -hacc -hnoomp']
        elif environ.name.startswith('PrgEnv-pgi'):
            self.build_system.fflags = [self._pgi_flags]

        self.variables = self._env_variables
        self.build_system.fflags += [self.mpiflag]
        super().setup(partition, environ, **job_opts)
