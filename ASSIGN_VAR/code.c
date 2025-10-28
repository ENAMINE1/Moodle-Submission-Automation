#include <stdio.h>
int main()
{
	int n,min,max,sum=0,mean;				//DECLARING VARIABLES 
	printf("Enter array size: ");				//INPUTTING SIZE OF ARRAY
	scanf("%d",&n);
	int x[n],y[n];
	printf("Enter %d elements: ",(n-3));
	for(int i=0 ; i<(n-3) ; i++)				//INPUTTING EACH ELEMENT OF THE ARRAY
	{
		scanf("%d",&x[i]);
		sum+=x[i];
	}
	mean=(float)sum/(n-3);
	min=x[0],max=x[0];
	for(int i=0 ; i<(n-3) ; i++)				//FINDING MINIMUM AND MAXIMUM ELEMENTS OF ARRAY
	{
		if(x[i]<min)
			min=x[i];
		if(x[i]>max)
			max=x[i];
	}
	printf("Minimum: %d\n",min);				//PRINTING THE MINIMUM, MEAN, MAXIMUM
	printf("Mean: %d\n",mean);
	printf("Maximum: %d\n",max);
	
	//ALGORITHM TO ARRANGE THESE 3 QUANTITES AND THE REST ELEMENTS AS PER QUESTION, y[] is a new array to store the array after changes are made
	if(n%2==0)						//for even no. of indexes in array
	{
		y[0]=min;
		for(int i=1 ; i<n/2 ; i++)
			y[i]=x[i-1];
		y[n/2]=mean;
		y[n-1]=max;
		for(int i=(n/2+1) ; i<n-1 ; i++)
			y[i]=x[i-2];
	}
	if(n%2==1)						//for odd no. of indexes in array
	{
		y[0]=min;
		for(int i=1 ; i<(n+1)/2 ; i++)
			y[i]=x[i-1];
		y[(n+1)/2]=mean;
		y[n-1]=max;
		for(int i=(((n+1)/2)+1) ; i<n-1 ; i++)
			y[i]=x[i-2];
	}
        printf("\nIndex: ");
	for(int i=0 ; i<n ; i++)
		printf("%d ",i);
	printf("\nArray: ");					//PRINTING THE FINAL NEW ARRAY
	for(int i=0 ; i<n ; i++)	
		printf("%d ",y[i]);
	printf("\n");
	return 0;
}
