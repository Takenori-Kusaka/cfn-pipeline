# cfn-pipline

CodePipeline to deploy Git managed Cloudfomation files after checking them with each testing tool.

## Installation

1. Create stack with template.yml

Create parameter file
./param.yml
```yaml
RepositoryName: CodeCommitRepoName
```
```sh
cfn-exec -i https://raw.githubusercontent.com/Takenori-Kusaka/cfn-pipeline/main/template.yml -p ./param.yml
```

2. Push CodeCommit

3. 
