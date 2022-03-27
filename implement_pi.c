
//code à ajouter après les include de base {
#include <stdio.h>
#include <stdlib.h>
int epsilon = 0; // proba to not pick the best
int alpha = 1; // learning rate

int is_acked = -1;
int sf = 12;
int minsf = 12;

int SFs[6] = {0};

int max(int* tab){
    int indice = 0;
    int max = tab[0];
    for(int i = 0 ; i<sizeof(tab) ; i++){
        if(tab[i] > max){
            max = tab[i];
            indice = i;
        }
    }
    return indice;
}
//}


//code à ajouter avant les fonctions {
void update(int now_sf,int acked){
    SFs[now_sf-7] = SFs[now_sf-7] + alpha * (acked - SFs[now_sf-7]);
}

int random_pick_sf(int minsf){
    int x = rand() %2;
    if (x > epsilon)
        return max(SFs) + 7;
    else{
        int x = (rand() % (13-minsf)) + minsf;
        return x;
    }

}
//}




void transmit(){

    for(int i = 0; i<10; i++){

        //code à ajouter juste à la place du choix de sf {
        if (is_acked > 0)
            update(sf,1);
        else
            update(sf,0);
        sf = random_pick_sf(minsf); 
        is_acked = rand() % 2;
        //}
        

        printf("tentative %d : Sf = %d, acked = %d\n",i,sf,is_acked);
        for(int j =0; j<6;j++){
            printf("%d: [%d]\n",j,SFs[j]);
        }
    }
}

int main(){
    transmit();
    return 1;
}